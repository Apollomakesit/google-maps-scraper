"""
Phase 2: The "Winning Formula" - Competitor Analysis Service.

Given a lead without a website, this module:
1. Finds the Top 3 competitors in the same Niche + Location (highest ratings).
2. Visits their websites with a headless browser.
3. Extracts design tokens (colors, structure, copywriting).
4. Saves structured JSON analysis to `market_intelligence` table.
"""

import asyncio
import json
import logging
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.database import get_supabase
from app.models import (
    NicheType,
    NICHE_SEARCH_QUERIES,
    NICHE_LABELS_RO,
)

logger = logging.getLogger(__name__)

# Common website sections to detect
SECTION_PATTERNS = {
    "hero": [
        r"hero", r"banner", r"jumbotron", r"slider", r"carousel",
        r"main-banner", r"home-banner",
    ],
    "services": [
        r"servic", r"what-we-do", r"offerings", r"features",
        r"ce-facem", r"servicii",
    ],
    "about": [
        r"about", r"despre", r"who-we-are", r"cine-suntem",
    ],
    "testimonials": [
        r"testimon", r"review", r"recenz", r"pareri",
        r"client", r"feedback",
    ],
    "gallery": [
        r"gallery", r"galerie", r"portofoliu", r"portfolio",
        r"before.?after", r"inainte.*dupa",
    ],
    "pricing": [
        r"pric", r"pret", r"tarif", r"cost", r"plan",
    ],
    "contact": [
        r"contact", r"get-in-touch", r"programare",
        r"appointment", r"rezerv",
    ],
    "blog": [
        r"blog", r"news", r"articol", r"stiri",
    ],
    "faq": [
        r"faq", r"intrebar", r"frequent", r"q&a",
    ],
    "team": [
        r"team", r"echipa", r"doctori", r"speciali",
    ],
    "map": [
        r"map", r"harta", r"locatie", r"google.*map",
    ],
}

# CSS color extraction patterns
HEX_COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b")
RGB_COLOR_PATTERN = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")
RGBA_COLOR_PATTERN = re.compile(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)")

# CTA button text patterns (Romanian + English)
CTA_PATTERNS = [
    r"programeaz[ăa]",
    r"rezer[vw][ăa]",
    r"sun[ăa].*acum",
    r"contacteaz[ăa]",
    r"cere.*ofert[ăa]",
    r"obține.*ofert[ăa]",
    r"afla.*mai.*mult",
    r"vezi.*servic",
    r"book\s*now",
    r"call\s*now",
    r"get\s*a?\s*quote",
    r"contact\s*us",
    r"schedule",
    r"learn\s*more",
    r"get\s*started",
    r"free\s*consult",
]


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def extract_colors_from_css(css_text: str) -> list[str]:
    """Extract all color values from CSS text."""
    colors = []

    # Extract hex colors
    for match in HEX_COLOR_PATTERN.finditer(css_text):
        color = match.group().lower()
        # Expand 3-digit hex to 6-digit
        if len(color) == 4:
            color = f"#{color[1]*2}{color[2]*2}{color[3]*2}"
        colors.append(color)

    # Extract rgb colors
    for match in RGB_COLOR_PATTERN.finditer(css_text):
        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        colors.append(rgb_to_hex(r, g, b))

    # Extract rgba colors
    for match in RGBA_COLOR_PATTERN.finditer(css_text):
        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        colors.append(rgb_to_hex(r, g, b))

    return colors


def filter_meaningful_colors(colors: list[str]) -> list[str]:
    """
    Filter out pure black, white, and near-transparent colors.
    Returns the most meaningful brand colors.
    """
    skip_colors = {
        "#000000", "#ffffff", "#fff", "#000",
        "#f8f9fa", "#e9ecef", "#dee2e6", "#ced4da",
        "#adb5bd", "#6c757d", "#495057", "#343a40", "#212529",
        "#f0f0f0", "#eeeeee", "#dddddd", "#cccccc", "#bbbbbb",
        "#999999", "#888888", "#777777", "#666666", "#555555",
        "#444444", "#333333", "#222222", "#111111",
    }

    filtered = [c for c in colors if c.lower() not in skip_colors]
    return filtered


async def fetch_page_content(url: str) -> Optional[str]:
    """
    Fetch a web page's HTML content using httpx.
    Falls back gracefully on errors.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
    }

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            verify=False,
            headers=headers,
        ) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Got status {response.status_code} for {url}")
                return None
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def analyze_website_html(html: str, base_url: str) -> dict:
    """
    Analyze a website's HTML to extract design tokens, structure, and copywriting.
    """
    soup = BeautifulSoup(html, "html.parser")

    # ─────────────────────────────────────────────
    # 1. COLOR PALETTE EXTRACTION
    # ─────────────────────────────────────────────
    all_colors: list[str] = []

    # Extract from inline styles
    for element in soup.find_all(style=True):
        style = element.get("style", "")
        all_colors.extend(extract_colors_from_css(style))

    # Extract from <style> tags
    for style_tag in soup.find_all("style"):
        if style_tag.string:
            all_colors.extend(extract_colors_from_css(style_tag.string))

    # Extract from style attributes on body/html
    body = soup.find("body")
    if body and body.get("style"):
        all_colors.extend(extract_colors_from_css(body["style"]))

    # Filter and rank colors
    meaningful_colors = filter_meaningful_colors(all_colors)
    color_counts = Counter(meaningful_colors)
    top_colors = [color for color, _ in color_counts.most_common(6)]
    dominant_color = top_colors[0] if top_colors else None

    # ─────────────────────────────────────────────
    # 2. FONT FAMILY EXTRACTION
    # ─────────────────────────────────────────────
    font_families: list[str] = []
    font_pattern = re.compile(r"font-family\s*:\s*([^;]+)")

    for element in soup.find_all(style=True):
        for match in font_pattern.finditer(element.get("style", "")):
            fonts = match.group(1).split(",")
            for font in fonts:
                font = font.strip().strip("'\"")
                if font and font not in ["inherit", "initial", "sans-serif", "serif", "monospace"]:
                    font_families.append(font)

    for style_tag in soup.find_all("style"):
        if style_tag.string:
            for match in font_pattern.finditer(style_tag.string):
                fonts = match.group(1).split(",")
                for font in fonts:
                    font = font.strip().strip("'\"")
                    if font and font not in ["inherit", "initial", "sans-serif", "serif", "monospace"]:
                        font_families.append(font)

    # Check Google Fonts links
    for link in soup.find_all("link"):
        href = link.get("href", "")
        if "fonts.googleapis.com" in href:
            family_match = re.search(r"family=([^&:]+)", href)
            if family_match:
                families = family_match.group(1).replace("+", " ").split("|")
                font_families.extend(families)

    font_counts = Counter(font_families)
    unique_fonts = [f for f, _ in font_counts.most_common(4)]

    # ─────────────────────────────────────────────
    # 3. WEBSITE STRUCTURE DETECTION
    # ─────────────────────────────────────────────
    detected_sections: list[str] = []
    page_text = soup.get_text(" ", strip=True).lower()
    all_ids_classes = []

    for tag in soup.find_all(True):
        tag_id = tag.get("id", "")
        tag_classes = " ".join(tag.get("class", []))
        all_ids_classes.append(f"{tag_id} {tag_classes}".lower())

    id_class_text = " ".join(all_ids_classes)
    combined_text = f"{page_text} {id_class_text}"

    for section_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                if section_name not in detected_sections:
                    detected_sections.append(section_name)
                break

    # Specific section checks
    has_before_after = bool(re.search(
        r"before.?after|inainte.*dupa|transformar", combined_text, re.IGNORECASE
    ))
    has_booking_form = bool(
        soup.find("form") and re.search(
            r"book|programar|rezerv|appointment|schedule",
            combined_text, re.IGNORECASE
        )
    )
    has_pricing = "pricing" in detected_sections
    has_blog = "blog" in detected_sections
    has_gallery = "gallery" in detected_sections
    has_testimonials = "testimonials" in detected_sections
    has_faq = "faq" in detected_sections
    has_map = "map" in detected_sections or bool(
        soup.find("iframe", src=re.compile(r"google.*maps|maps.*google", re.IGNORECASE))
    )

    # ─────────────────────────────────────────────
    # 4. COPYWRITING EXTRACTION
    # ─────────────────────────────────────────────
    # H1 headlines
    h1_tags = soup.find_all("h1")
    h1_headline = ""
    if h1_tags:
        h1_text = h1_tags[0].get_text(strip=True)
        if len(h1_text) > 3:
            h1_headline = h1_text[:200]

    # H2 headlines
    h2_headlines = []
    for h2 in soup.find_all("h2"):
        text = h2.get_text(strip=True)
        if len(text) > 3 and len(text) < 200:
            h2_headlines.append(text)
    h2_headlines = h2_headlines[:8]

    # CTA buttons
    cta_buttons = []
    button_elements = soup.find_all(["button", "a"])
    for btn in button_elements:
        btn_text = btn.get_text(strip=True)
        btn_classes = " ".join(btn.get("class", []))
        btn_href = btn.get("href", "")

        is_cta = False
        # Check if it looks like a CTA
        if any(cls in btn_classes.lower() for cls in ["btn", "button", "cta", "action"]):
            is_cta = True
        for pattern in CTA_PATTERNS:
            if re.search(pattern, btn_text, re.IGNORECASE):
                is_cta = True
                break

        if is_cta and btn_text and len(btn_text) > 2 and len(btn_text) < 60:
            if btn_text not in cta_buttons:
                cta_buttons.append(btn_text)

    cta_buttons = cta_buttons[:6]

    # Value propositions (from headings and strong text)
    value_props = []
    for tag in soup.find_all(["h2", "h3", "strong", "b"]):
        text = tag.get_text(strip=True)
        if 5 < len(text) < 100:
            value_props.append(text)
    value_props = list(dict.fromkeys(value_props))[:6]

    # Determine tone
    tone = "professional"
    informal_patterns = ["hey", "salut", "buna", "super", "wow", "cool"]
    formal_patterns = ["profesional", "experienta", "calitate", "excelenta", "expertiza"]
    if any(p in page_text for p in informal_patterns):
        tone = "casual"
    elif any(p in page_text for p in formal_patterns):
        tone = "professional"

    # ─────────────────────────────────────────────
    # 5. META INFORMATION
    # ─────────────────────────────────────────────
    meta_title = ""
    title_tag = soup.find("title")
    if title_tag:
        meta_title = title_tag.get_text(strip=True)

    meta_description = ""
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    if meta_desc_tag:
        meta_description = meta_desc_tag.get("content", "")

    og_image = ""
    og_img_tag = soup.find("meta", property="og:image")
    if og_img_tag:
        og_image = og_img_tag.get("content", "")
        if og_image and not og_image.startswith("http"):
            og_image = urljoin(base_url, og_image)

    return {
        "design_tokens": {
            "color_palette": top_colors,
            "dominant_color": dominant_color,
            "font_families": unique_fonts,
        },
        "structure": {
            "sections": detected_sections,
            "has_before_after": has_before_after,
            "has_booking_form": has_booking_form,
            "has_pricing": has_pricing,
            "has_blog": has_blog,
            "has_gallery": has_gallery,
            "has_testimonials": has_testimonials,
            "has_faq": has_faq,
            "has_map": has_map,
        },
        "copywriting": {
            "h1_headline": h1_headline,
            "h2_headlines": h2_headlines,
            "cta_buttons": cta_buttons,
            "value_propositions": value_props,
            "tone": tone,
        },
        "meta": {
            "title": meta_title,
            "description": meta_description,
            "og_image": og_image,
        },
    }


async def find_top_competitors(
    niche: str,
    location: str,
    exclude_place_id: Optional[str] = None,
    top_n: int = 3,
) -> list[dict]:
    """
    Find the top N competitors in the same niche + location
    from Supabase leads that DO have websites.
    Falls back to Google Maps search if not enough in DB.
    """
    db = get_supabase()
    competitors = []

    # First, try to find competitors from our existing scraped data
    try:
        query = (
            db.table("leads")
            .select("*")
            .eq("niche", niche)
            .ilike("city", f"%{location}%")
            .neq("website_status", "missing")
            .neq("website_status", "404")
            .order("review_rating", desc=True)
            .order("review_count", desc=True)
            .limit(top_n * 2)
        )

        if exclude_place_id:
            query = query.neq("place_id", exclude_place_id)

        result = query.execute()

        if result.data:
            for row in result.data[:top_n]:
                competitors.append({
                    "name": row.get("name", ""),
                    "website_url": row.get("website_url", ""),
                    "google_maps_link": row.get("google_maps_link", ""),
                    "rating": float(row.get("review_rating", 0)),
                    "review_count": row.get("review_count", 0),
                })
    except Exception as e:
        logger.warning(f"DB competitor search failed: {e}")

    # If not enough competitors from DB, search Google Maps
    if len(competitors) < top_n:
        try:
            from app.services.lead_scraper import scrape_google_maps_api

            queries = NICHE_SEARCH_QUERIES.get(niche, [niche])
            search_query = queries[0] if queries else niche

            entries = await scrape_google_maps_api(search_query, location, 20)

            # Filter to those WITH websites, sort by rating
            with_website = [
                e for e in entries
                if (e.get("web_site") or "").strip()
                and not any(
                    d in (e.get("web_site") or "").lower()
                    for d in ["facebook.com", "instagram.com", "twitter.com"]
                )
            ]

            with_website.sort(
                key=lambda x: (-(x.get("review_rating") or 0), -(x.get("review_count") or 0))
            )

            existing_names = {c["name"].lower() for c in competitors}

            for entry in with_website:
                if len(competitors) >= top_n:
                    break
                name = (entry.get("title") or "").strip()
                if name.lower() in existing_names:
                    continue
                existing_names.add(name.lower())

                competitors.append({
                    "name": name,
                    "website_url": (entry.get("web_site") or "").strip(),
                    "google_maps_link": entry.get("link", ""),
                    "rating": float(entry.get("review_rating") or 0),
                    "review_count": entry.get("review_count") or 0,
                })

        except Exception as e:
            logger.warning(f"Google Maps competitor search failed: {e}")

    return competitors[:top_n]


def generate_common_patterns(competitor_analyses: list[dict]) -> dict:
    """
    Aggregate patterns across all analyzed competitors to find
    the "Winning Formula".
    """
    all_colors: list[str] = []
    all_sections: list[str] = []
    all_ctas: list[str] = []
    all_props: list[str] = []
    all_tones: list[str] = []

    for comp in competitor_analyses:
        dt = comp.get("design_tokens", {})
        st = comp.get("structure", {})
        cw = comp.get("copywriting", {})

        all_colors.extend(dt.get("color_palette", []))
        all_sections.extend(st.get("sections", []))
        all_ctas.extend(cw.get("cta_buttons", []))
        all_props.extend(cw.get("value_propositions", []))
        all_tones.append(cw.get("tone", "professional"))

    # Find most common colors
    color_counts = Counter(all_colors)
    dominant_colors = [c for c, _ in color_counts.most_common(4)]

    # Find sections that appear in 2+ competitors
    section_counts = Counter(all_sections)
    common_sections = [s for s, count in section_counts.most_common() if count >= 2]
    if not common_sections:
        common_sections = [s for s, _ in section_counts.most_common(5)]

    # Common CTAs
    cta_counts = Counter(all_ctas)
    common_ctas = [c for c, _ in cta_counts.most_common(4)]

    # Messaging themes
    prop_counts = Counter(all_props)
    themes = [p for p, _ in prop_counts.most_common(5)]

    # Recommended structure (merge all detected sections in logical order)
    section_order = [
        "hero", "services", "about", "gallery", "testimonials",
        "pricing", "team", "faq", "blog", "contact", "map",
    ]
    recommended = [s for s in section_order if s in set(all_sections)]

    # Generate Romanian summary
    summary_parts = []
    if dominant_colors:
        color_str = ", ".join(dominant_colors[:3])
        summary_parts.append(f"Culorile dominante sunt {color_str}")

    if common_sections:
        sections_str = ", ".join(common_sections[:4])
        summary_parts.append(f"Secțiunile comune: {sections_str}")

    if common_ctas:
        cta_str = ", ".join(f'"{c}"' for c in common_ctas[:3])
        summary_parts.append(f"Textele CTA frecvente: {cta_str}")

    if themes:
        themes_str = ", ".join(f'"{t}"' for t in themes[:3])
        summary_parts.append(f"Teme de mesagerie: {themes_str}")

    summary_ro = ". ".join(summary_parts) + "." if summary_parts else "Analiza în curs."

    return {
        "dominant_colors": dominant_colors,
        "common_sections": common_sections,
        "common_cta_text": common_ctas,
        "messaging_themes": themes,
        "recommended_structure": recommended,
        "summary_ro": summary_ro,
    }


def generate_strategy_summary(
    lead_name: str,
    niche: str,
    common_patterns: dict,
    competitors: list[dict],
) -> str:
    """Generate a Romanian strategy summary for the lead."""
    niche_label = NICHE_LABELS_RO.get(niche, niche)
    num_competitors = len(competitors)

    lines = [
        f"## Strategie pentru: {lead_name}",
        f"**Nișă:** {niche_label}",
        f"**Competitori analizați:** {num_competitors}",
        "",
    ]

    # Colors
    colors = common_patterns.get("dominant_colors", [])
    if colors:
        lines.append(f"### Paleta de Culori Recomandată")
        lines.append(f"Competitorii folosesc predominant: {', '.join(colors[:3])}")
        lines.append("")

    # Structure
    sections = common_patterns.get("recommended_structure", [])
    if sections:
        lines.append(f"### Structura Site-ului Recomandat")
        for i, section in enumerate(sections, 1):
            section_labels = {
                "hero": "Secțiune Hero cu imagine puternică",
                "services": "Lista de Servicii",
                "about": "Despre Noi / Echipă",
                "gallery": "Galerie Foto / Portofoliu",
                "testimonials": "Testimoniale / Recenzii",
                "pricing": "Prețuri / Pachete",
                "team": "Echipa / Specialiști",
                "faq": "Întrebări Frecvente",
                "blog": "Blog / Articole",
                "contact": "Formular de Contact",
                "map": "Hartă Google Maps",
            }
            label = section_labels.get(section, section.title())
            lines.append(f"{i}. {label}")
        lines.append("")

    # CTAs
    ctas = common_patterns.get("common_cta_text", [])
    if ctas:
        lines.append(f"### Butoane Call-to-Action Recomandate")
        for cta in ctas[:3]:
            lines.append(f"- \"{cta}\"")
        lines.append("")

    # Competitive advantages
    lines.append("### Avantaje Competitive")
    lines.append(
        "Deoarece acest business NU are site web, crearea unui site modern "
        "cu elementele de mai sus va oferi un avantaj imediat față de "
        "competitorii care deja au prezență online."
    )

    return "\n".join(lines)


async def analyze_competitors_for_lead(
    lead_id: str,
    intelligence_id: str,
    top_n: int = 3,
) -> dict:
    """
    Main competitor analysis pipeline for a specific lead.
    """
    db = get_supabase()

    try:
        # Update status to in_progress
        db.table("market_intelligence").update({
            "analysis_status": "in_progress",
        }).eq("id", intelligence_id).execute()

        # Also update the lead status
        db.table("leads").update({
            "status": "analyzing",
        }).eq("id", lead_id).execute()

        # Fetch the lead
        lead_result = db.table("leads").select("*").eq("id", lead_id).single().execute()
        lead = lead_result.data

        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        niche = lead.get("niche", "other")
        city = lead.get("city", "București")

        # Find top competitors
        competitors = await find_top_competitors(
            niche=niche,
            location=city,
            exclude_place_id=lead.get("place_id"),
            top_n=top_n,
        )

        if not competitors:
            raise ValueError(f"No competitors found for {niche} in {city}")

        logger.info(f"Found {len(competitors)} competitors for lead {lead_id}")

        # Analyze each competitor's website
        analyzed_competitors = []
        for rank, comp in enumerate(competitors, 1):
            website_url = comp.get("website_url", "")
            if not website_url:
                continue

            logger.info(f"Analyzing competitor #{rank}: {comp['name']} ({website_url})")

            # Fetch the website
            html = await fetch_page_content(website_url)

            if html:
                analysis = analyze_website_html(html, website_url)
            else:
                analysis = {
                    "design_tokens": {"color_palette": [], "dominant_color": None, "font_families": []},
                    "structure": {
                        "sections": [], "has_before_after": False, "has_booking_form": False,
                        "has_pricing": False, "has_blog": False, "has_gallery": False,
                        "has_testimonials": False, "has_faq": False, "has_map": False,
                    },
                    "copywriting": {
                        "h1_headline": "", "h2_headlines": [], "cta_buttons": [],
                        "value_propositions": [], "tone": "unknown",
                    },
                    "meta": {"title": "", "description": "", "og_image": ""},
                }

            competitor_data = {
                "name": comp["name"],
                "website_url": website_url,
                "google_maps_link": comp.get("google_maps_link", ""),
                "rating": comp.get("rating", 0),
                "review_count": comp.get("review_count", 0),
                "rank": rank,
                **analysis,
            }

            analyzed_competitors.append(competitor_data)

            # Delay between requests
            await asyncio.sleep(2)

        # Generate common patterns
        common_patterns = generate_common_patterns(analyzed_competitors)

        # Generate strategy summary
        strategy = generate_strategy_summary(
            lead_name=lead.get("name", "Unknown"),
            niche=niche,
            common_patterns=common_patterns,
            competitors=analyzed_competitors,
        )

        # Save results to Supabase
        now = datetime.now(timezone.utc).isoformat()

        db.table("market_intelligence").update({
            "competitors": analyzed_competitors,
            "common_patterns": common_patterns,
            "strategy_summary": strategy,
            "analysis_status": "completed",
            "analyzed_at": now,
        }).eq("id", intelligence_id).execute()

        # Update lead status
        db.table("leads").update({
            "status": "analyzed",
        }).eq("id", lead_id).execute()

        logger.info(f"Competitor analysis completed for lead {lead_id}")

        return {
            "intelligence_id": intelligence_id,
            "lead_id": lead_id,
            "status": "completed",
            "competitors_analyzed": len(analyzed_competitors),
            "common_patterns": common_patterns,
            "strategy_summary": strategy,
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Competitor analysis failed for lead {lead_id}: {error_msg}")

        try:
            db.table("market_intelligence").update({
                "analysis_status": "failed",
                "error_message": error_msg,
            }).eq("id", intelligence_id).execute()

            db.table("leads").update({
                "status": "new",
            }).eq("id", lead_id).execute()
        except Exception:
            pass

        return {
            "intelligence_id": intelligence_id,
            "lead_id": lead_id,
            "status": "failed",
            "error": error_msg,
        }
