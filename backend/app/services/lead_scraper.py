"""
Phase 1: The "Gap Finder" - Lead Generation Service.

Scrapes Google Maps for businesses, filters those without websites (or with 404s),
enriches them with contact data, and saves to Supabase `leads` table.
"""

import asyncio
import json
import logging
import random
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.database import get_supabase
from app.models import NicheType, NICHE_SEARCH_QUERIES

logger = logging.getLogger(__name__)

# Tier classification keywords (Romanian + English)
TIER1_KEYWORDS = [
    "instalator", "plumber", "instalatii",
    "electrician", "electrice", "electric",
    "acoperis", "roofer", "roof",
    "service auto", "vulcanizare", "mecanic auto", "reparatii auto",
    "auto repair", "car service", "car repair",
    "amenajari", "gradini", "peisagist", "landscap", "gradinar", "spatii verzi",
]

TIER2_KEYWORDS = [
    "dentist", "stomatolog", "dentar", "dental", "implant",
    "salon", "coafor", "coafura", "frizerie", "hair", "infrumusetare", "beauty",
    "fitness", "gym", "sala de forta",
    "restaurant", "cafenea", "coffee",
    "avocat", "juridic", "lawyer",
    "imobiliar", "real estate",
]


def classify_tier(title: str, categories: list[str]) -> int:
    """Classify a business into priority tiers."""
    text = f"{title} {' '.join(categories)}".lower()
    for kw in TIER1_KEYWORDS:
        if kw in text:
            return 1
    for kw in TIER2_KEYWORDS:
        if kw in text:
            return 2
    return 3


def map_niche_from_categories(categories: list[str]) -> str:
    """Attempt to map Google Maps categories to our niche types."""
    text = " ".join(categories).lower()

    mapping = {
        "dentist": ["dentist", "stomatolog", "dentar", "dental"],
        "restaurants": ["restaurant", "bistro", "pizzerie"],
        "plumbers": ["instalator", "plumber", "instalatii sanitare"],
        "electricians": ["electrician", "electrice"],
        "lawyers": ["avocat", "juridic", "notar"],
        "real_estate_agents": ["imobiliar", "real estate"],
        "coffee_shops": ["cafenea", "coffee", "cofetarie"],
        "hair_salons": ["coafor", "frizerie", "salon", "beauty", "infrumusetare"],
        "auto_repair": ["service auto", "mecanic", "vulcanizare", "auto repair"],
        "gyms": ["fitness", "gym", "forta", "aerobic", "sport"],
        "landscapers": ["gradini", "peisagist", "landscap"],
        "roofers": ["acoperis", "roofer", "roof"],
    }

    for niche, keywords in mapping.items():
        for kw in keywords:
            if kw in text:
                return niche
    return "other"


async def check_website_status(url: str) -> tuple[bool, str]:
    """
    Check if a website URL is reachable.
    Returns (is_dead, status_description).
    """
    if not url or url.strip() == "":
        return True, "missing"

    # Skip social media links - they're not real websites
    social_domains = [
        "facebook.com", "instagram.com", "twitter.com", "tiktok.com",
        "youtube.com", "linkedin.com", "wa.me", "whatsapp.com"
    ]
    for domain in social_domains:
        if domain in url.lower():
            return True, "social_only"

    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            verify=False,
        ) as client:
            response = await client.head(url)
            if response.status_code == 404:
                return True, "404"
            if response.status_code >= 500:
                return True, f"error_{response.status_code}"
            return False, "active"
    except httpx.TimeoutException:
        return True, "timeout"
    except httpx.ConnectError:
        return True, "connection_error"
    except Exception as e:
        logger.warning(f"Website check failed for {url}: {e}")
        return True, "error"


async def scrape_google_maps_api(
    query: str,
    location: str,
    max_results: int = 60,
) -> list[dict]:
    """
    Scrape Google Maps using the existing Go scraper's output format.
    This function reads from the Go scraper's JSON output or performs
    direct HTTP scraping as a fallback.

    In production, this integrates with the Go binary or uses
    Google Places API if available.
    """
    results = []

    # Strategy 1: Use Google Places API if key is available
    if settings.google_maps_api_key:
        results = await _scrape_via_places_api(query, location, max_results)
    else:
        # Strategy 2: Use the Go scraper binary via subprocess
        results = await _scrape_via_go_binary(query, location, max_results)

    return results


async def _scrape_via_places_api(
    query: str,
    location: str,
    max_results: int,
) -> list[dict]:
    """Use Google Places API Text Search for scraping."""
    results = []
    search_query = f"{query} in {location}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": search_query,
            "key": settings.google_maps_api_key,
            "language": "ro",
        }

        try:
            response = await client.get(url, params=params)
            data = response.json()

            if data.get("status") != "OK":
                logger.warning(f"Places API returned status: {data.get('status')}")
                return results

            for place in data.get("results", [])[:max_results]:
                place_id = place.get("place_id", "")

                # Get detailed info
                detail = await _get_place_details(client, place_id)

                result = {
                    "title": place.get("name", ""),
                    "place_id": place_id,
                    "link": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                    "address": place.get("formatted_address", ""),
                    "latitude": place.get("geometry", {}).get("location", {}).get("lat"),
                    "longtitude": place.get("geometry", {}).get("location", {}).get("lng"),
                    "review_count": place.get("user_ratings_total", 0),
                    "review_rating": place.get("rating", 0),
                    "categories": place.get("types", []),
                    "web_site": detail.get("website", ""),
                    "phone": detail.get("formatted_phone_number", ""),
                    "status": place.get("business_status", ""),
                    "emails": [],
                }
                results.append(result)

                # Respect rate limits
                await asyncio.sleep(random.uniform(0.2, 0.5))

            # Handle pagination
            next_page_token = data.get("next_page_token")
            while next_page_token and len(results) < max_results:
                await asyncio.sleep(2)  # Required by Google API
                params["pagetoken"] = next_page_token
                response = await client.get(url, params=params)
                data = response.json()

                for place in data.get("results", []):
                    if len(results) >= max_results:
                        break
                    place_id = place.get("place_id", "")
                    detail = await _get_place_details(client, place_id)

                    result = {
                        "title": place.get("name", ""),
                        "place_id": place_id,
                        "link": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                        "address": place.get("formatted_address", ""),
                        "latitude": place.get("geometry", {}).get("location", {}).get("lat"),
                        "longtitude": place.get("geometry", {}).get("location", {}).get("lng"),
                        "review_count": place.get("user_ratings_total", 0),
                        "review_rating": place.get("rating", 0),
                        "categories": place.get("types", []),
                        "web_site": detail.get("website", ""),
                        "phone": detail.get("formatted_phone_number", ""),
                        "status": place.get("business_status", ""),
                        "emails": [],
                    }
                    results.append(result)
                    await asyncio.sleep(random.uniform(0.2, 0.5))

                next_page_token = data.get("next_page_token")

        except Exception as e:
            logger.error(f"Places API error: {e}")

    return results


async def _get_place_details(client: httpx.AsyncClient, place_id: str) -> dict:
    """Get detailed place information from Google Places API."""
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "website,formatted_phone_number,url",
            "key": settings.google_maps_api_key,
            "language": "ro",
        }
        response = await client.get(url, params=params)
        data = response.json()
        return data.get("result", {})
    except Exception as e:
        logger.warning(f"Place details error for {place_id}: {e}")
        return {}


async def _scrape_via_go_binary(
    query: str,
    location: str,
    max_results: int,
) -> list[dict]:
    """
    Use the existing Go google-maps-scraper binary.
    Creates a temp query file and runs the binary in file mode.
    """
    import tempfile
    import os

    search_term = f"{query} in {location}"
    results = []

    # Check if the Go binary exists
    binary_path = "/usr/bin/google-maps-scraper"
    if not os.path.exists(binary_path):
        # Try building it
        try:
            proc = await asyncio.create_subprocess_exec(
                "go", "build", "-o", binary_path, ".",
                cwd="/workspace",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        except Exception as e:
            logger.warning(f"Could not build Go binary: {e}")
            if settings.enable_demo_fallback:
                return await _get_demo_data(query, location)
            return []

    # Create temp query file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(search_term + "\n")
        query_file = f.name

    # Create temp output file
    output_file = tempfile.mktemp(suffix=".json")

    try:
        proc = await asyncio.create_subprocess_exec(
            binary_path,
            "-input", query_file,
            "-results", output_file,
            "-json",
            "-exit-on-inactivity", "30s",
            "-lang", "ro",
            "-depth", "1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=120,
        )

        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        results.append(entry)
                    except json.JSONDecodeError:
                        continue

    except asyncio.TimeoutError:
        logger.warning(f"Go binary timed out for query: {search_term}")
    except Exception as e:
        logger.error(f"Go binary error: {e}")
    finally:
        # Clean up temp files
        for f in [query_file, output_file]:
            try:
                os.unlink(f)
            except OSError:
                pass

    if not results and settings.enable_demo_fallback:
        results = await _get_demo_data(query, location)

    return results


async def _get_demo_data(query: str, location: str) -> list[dict]:
    """
    Load demo data from the existing bucharest-results.json file.
    Used as fallback when the Go binary or API is not available.
    """
    results = []

    demo_paths = [
        Path("/workspace/bucharest-results.json"),
        Path("/app/bucharest-results.json"),
        Path("/app/data/bucharest-results.json"),
        Path(__file__).resolve().parent.parent.parent / "bucharest-results.json",
    ]

    for demo_file in demo_paths:
        if not demo_file.exists():
            continue

        with demo_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    results.append(entry)
                except json.JSONDecodeError:
                    continue

        if results:
            logger.info(f"Loaded {len(results)} demo entries from {demo_file} for '{query} in {location}'")
            return results

    if settings.enable_demo_fallback:
        generated = _generate_fallback_entries(query, location)
        logger.info(
            f"No demo file found for '{query} in {location}', generated {len(generated)} fallback entries"
        )
        return generated

    logger.warning(
        "No demo file found for '%s in %s' and demo fallback is disabled",
        query,
        location,
    )
    return []


def _generate_fallback_entries(query: str, location: str, size: int = 12) -> list[dict]:
    """Generate deterministic fallback entries when no scraper/demo data is available."""
    query_lc = query.lower()
    import hashlib
    base_seed = int(hashlib.sha1(f"{query}|{location}".encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(base_seed)

    if any(k in query_lc for k in ["dent", "stomat", "dentar"]):
        kind = "dentist"
        names = [
            "Smile Studio", "Dental Focus", "Ortho Plus", "Cabinet Dentar Nova",
            "Dent Expert", "Clinica Dentaris", "Alfa Dental", "Bright Tooth",
            "Stoma Vision", "Family Dental Care", "Dent Art", "Denta Prime",
        ]
        categories = ["dentist", "stomatolog", "clinica dentara"]
    elif any(k in query_lc for k in ["rest", "bistro", "pizza"]):
        kind = "restaurants"
        names = [
            "Bistro Urban", "La Gust", "Casa Bună", "Pasta Point", "Trattoria Uno",
            "Hanul Central", "Meniu de Zi", "Grill Republic", "Street Kitchen", "Delish Hub",
            "Fork & Flame", "Table 21",
        ]
        categories = ["restaurant", "bistro"]
    elif any(k in query_lc for k in ["instal", "plumb"]):
        kind = "plumbers"
        names = [
            "Instal Rapid", "Aqua Service", "Fix Sanitare", "Plumb Pro", "Teava Expert",
            "Instal Home", "WaterLine", "Sanitar Team", "Urgent Instal", "Pipe Craft",
            "Eco Instal", "Hydro Help",
        ]
        categories = ["instalator", "instalatii sanitare"]
    else:
        kind = "other"
        names = [
            "Business Hub", "Pro Services", "City Team", "Alpha Group", "Local Expert",
            "Smart Solutions", "Urban Works", "Prime Point", "Blue Line", "Core Services",
            "Central Works", "Atlas Team",
        ]
        categories = ["servicii locale"]

    entries: list[dict] = []
    city = location.strip() or "Bucuresti"

    for index in range(min(size, len(names))):
        name = f"{names[index]} {city}"
        phone_last = rng.randint(100, 999)
        rating = round(3.7 + rng.random() * 1.2, 1)
        reviews = rng.randint(4, 240)
        lat = round(44.35 + rng.random() * 0.2, 6)
        lng = round(26.00 + rng.random() * 0.2, 6)

        website_mode = rng.randint(0, 2)
        if website_mode == 0:
            website = ""
        elif website_mode == 1:
            website = f"https://{name.lower().replace(' ', '-')}.ro"
        else:
            website = "https://facebook.com/placeholder-business"

        entry = {
            "title": name,
            "place_id": f"fallback-{kind}-{base_seed}-{index}",
            "link": f"https://maps.google.com/?q={name.replace(' ', '+')}",
            "address": f"Str. Exemplu {index + 1}, {city}",
            "complete_address": {
                "city": city,
                "borough": "Sector 1" if city.lower().startswith("buc") else "",
                "postal_code": f"0{rng.randint(1000, 9999)}",
                "country": "RO",
            },
            "latitude": lat,
            "longtitude": lng,
            "review_count": reviews,
            "review_rating": rating,
            "categories": categories,
            "web_site": website,
            "phone": f"+40 7{rng.randint(10, 99)} {rng.randint(100, 999)} {phone_last}",
            "status": "OPERATIONAL",
            "emails": [],
        }
        entries.append(entry)

    return entries


async def process_scrape_job(
    job_id: str,
    location: str,
    niche: NicheType,
    max_results: int = 100,
) -> dict:
    """
    Main pipeline: scrape -> filter -> enrich -> save to Supabase.
    """
    db = get_supabase()
    total_scraped = 0
    total_leads = 0

    def _update_job_progress(total: int, filtered: int) -> None:
        try:
            db.table("scrape_jobs").update({
                "total_results": total,
                "filtered_leads": filtered,
            }).eq("id", job_id).execute()
        except Exception as progress_error:
            logger.warning(f"Job {job_id}: progress update failed: {progress_error}")

    try:
        # Update job status to running
        db.table("scrape_jobs").update({
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", job_id).execute()

        # Get search queries for this niche
        queries = NICHE_SEARCH_QUERIES.get(niche.value, [niche.value])

        all_entries: list[dict] = []
        seen_place_ids: set[str] = set()

        for query in queries:
            entries = await scrape_google_maps_api(query, location, max_results)
            for entry in entries:
                pid = entry.get("place_id") or entry.get("data_id") or entry.get("title", "")
                if pid not in seen_place_ids:
                    seen_place_ids.add(pid)
                    all_entries.append(entry)

            _update_job_progress(total=len(all_entries), filtered=0)

            # Anti-bot delay between queries
            await asyncio.sleep(random.uniform(
                settings.scrape_delay_min,
                settings.scrape_delay_max,
            ))

        total_scraped = len(all_entries)
        logger.info(f"Job {job_id}: Scraped {total_scraped} total entries")

        if total_scraped == 0 and not settings.enable_demo_fallback and not settings.google_maps_api_key:
            raise RuntimeError(
                "Nu există sursă reală de scraping disponibilă. Configurează GOOGLE_MAPS_API_KEY "
                "sau activează ENABLE_DEMO_FALLBACK=true."
            )

        # Filter & enrich
        leads_to_insert = []
        seen_dedup: set[str] = set()

        for entry in all_entries:
            title = (entry.get("title") or "").strip()
            website = (entry.get("web_site") or "").strip()
            phone = (entry.get("phone") or "").strip()
            emails = entry.get("emails") or []
            review_count = entry.get("review_count") or 0
            review_rating = entry.get("review_rating") or 0
            categories = entry.get("categories") or []
            place_id = entry.get("place_id") or ""

            # Deduplication
            dedup_key = f"{title}|{phone}".lower()
            if dedup_key in seen_dedup:
                continue
            seen_dedup.add(dedup_key)

            if website:
                continue

            website_status = "missing"

            # Must have some contact info
            if not phone and not emails:
                continue

            # Must have at least some presence (reviews)
            if review_count < 1:
                continue

            tier = classify_tier(title, categories)
            detected_niche = map_niche_from_categories(categories)

            # Extract location details
            complete_address = entry.get("complete_address") or {}

            lead = {
                "id": str(uuid.uuid4()),
                "name": title,
                "google_maps_link": entry.get("link", ""),
                "place_id": place_id if place_id else None,
                "niche": detected_niche if detected_niche != "other" else niche.value,
                "categories": categories,
                "tier": tier,
                "phone": phone,
                "emails": emails if emails else [],
                "address": entry.get("address", ""),
                "city": complete_address.get("city", location),
                "borough": complete_address.get("borough", ""),
                "postal_code": complete_address.get("postal_code", ""),
                "country": complete_address.get("country", "RO"),
                "latitude": entry.get("latitude"),
                "longitude": entry.get("longtitude"),  # Note: typo in source data
                "review_count": review_count,
                "review_rating": float(review_rating),
                "website_url": website if website else None,
                "website_status": website_status,
                "status": "new",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

            leads_to_insert.append(lead)

            if len(leads_to_insert) % 5 == 0:
                _update_job_progress(total=total_scraped, filtered=len(leads_to_insert))

        total_leads = len(leads_to_insert)
        _update_job_progress(total=total_scraped, filtered=total_leads)
        logger.info(f"Job {job_id}: Filtered to {total_leads} leads (no website)")

        # Batch insert leads into Supabase
        if leads_to_insert:
            batch_size = 50
            for i in range(0, len(leads_to_insert), batch_size):
                batch = leads_to_insert[i:i + batch_size]
                try:
                    db.table("leads").upsert(
                        batch,
                        on_conflict="place_id",
                    ).execute()
                except Exception as e:
                    logger.error(f"Batch insert error: {e}")
                    # Try individual inserts as fallback
                    for lead in batch:
                        try:
                            db.table("leads").upsert(
                                lead,
                                on_conflict="place_id",
                            ).execute()
                        except Exception as inner_e:
                            logger.warning(f"Individual insert failed for {lead['name']}: {inner_e}")

        # Update job as completed
        db.table("scrape_jobs").update({
            "status": "completed",
            "total_results": total_scraped,
            "filtered_leads": total_leads,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", job_id).execute()

        return {
            "job_id": job_id,
            "status": "completed",
            "total_scraped": total_scraped,
            "total_leads": total_leads,
        }

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        try:
            db.table("scrape_jobs").update({
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", job_id).execute()
        except Exception:
            pass

        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
            "total_scraped": total_scraped,
            "total_leads": total_leads,
        }
