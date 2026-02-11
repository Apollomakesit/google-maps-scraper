#!/usr/bin/env python3
"""
Filter Google Maps scraper JSON results to find leads:
- WITHOUT a website (your upsale opportunity)
- WITH reviews (established businesses)
- Has phone number or email

Outputs a clean CSV with the most important columns for outreach.
"""

import json
import csv
import sys
import os
from collections import defaultdict

INPUT_FILE = "bucharest-results.json"
OUTPUT_ALL = "bucharest-leads-all.csv"
OUTPUT_TIER1 = "bucharest-leads-tier1.csv"
OUTPUT_TIER2 = "bucharest-leads-tier2.csv"

# Tier classification keywords (Romanian + English)
TIER1_KEYWORDS = [
    "instalator", "plumber", "instalatii",
    "electrician", "electrice", "electric",
    "acoperis", "roofer", "roof",
    "service auto", "vulcanizare", "mecanic auto", "reparatii auto", "auto repair", "car service", "car repair",
    "amenajari", "gradini", "peisagist", "landscap", "gradinar", "spatii verzi",
]

TIER2_KEYWORDS = [
    "dentist", "stomatolog", "dentar", "dental", "implant",
    "salon", "coafor", "coafura", "frizerie", "hair", "infrumusetare", "beauty",
    "fitness"
]

def classify_tier(title, categories):
    """Classify a business into tiers based on title and categories."""
    text = f"{title} {' '.join(categories)}".lower()
    for kw in TIER1_KEYWORDS:
        if kw in text:
            return 1
    for kw in TIER2_KEYWORDS:
        if kw in text:
            return 2
    return 3  # Unknown/other


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} not found. Run the scraper first.")
        sys.exit(1)

    # Load JSON results (one JSON object per line)
    entries = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    print(f"Total scraped entries: {len(entries)}")

    # Filter: NO website, HAS reviews, HAS phone or email
    leads = []
    seen = set()  # deduplicate by title+phone
    for e in entries:
        website = (e.get("web_site") or "").strip()
        review_count = e.get("review_count", 0) or 0
        phone = (e.get("phone") or "").strip()
        emails = e.get("emails") or []
        title = (e.get("title") or "").strip()

        # Skip if has website
        if website:
            continue

        # Must have at least 1 review
        if review_count < 1:
            continue

        # Must have phone or email
        if not phone and not emails:
            continue

        # Deduplicate
        dedup_key = f"{title}|{phone}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        tier = classify_tier(title, e.get("categories") or [])
        leads.append({
            "tier": tier,
            "title": title,
            "category": e.get("category", ""),
            "phone": phone,
            "emails": "; ".join(emails) if emails else "",
            "review_count": review_count,
            "review_rating": e.get("review_rating", 0),
            "address": e.get("address", ""),
            "google_maps_link": e.get("link", ""),
            "status": e.get("status", ""),
        })

    # Sort by tier (1 first), then by review count descending
    leads.sort(key=lambda x: (x["tier"], -x["review_count"]))

    print(f"\nFiltered leads (no website, has reviews, has contact): {len(leads)}")

    # Stats
    tier_counts = defaultdict(int)
    for l in leads:
        tier_counts[l["tier"]] += 1
    print(f"  Tier 1 (Emergency & High Value): {tier_counts[1]}")
    print(f"  Tier 2 (Visual & Booking):       {tier_counts[2]}")
    print(f"  Tier 3 (Other/Unclassified):     {tier_counts[3]}")

    # Write CSVs
    fieldnames = ["tier", "title", "category", "phone", "emails",
                   "review_count", "review_rating", "address", "google_maps_link", "status"]

    def write_csv(filename, data):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"  Written {len(data)} leads to {filename}")

    # All leads
    write_csv(OUTPUT_ALL, leads)

    # Tier 1 only
    tier1 = [l for l in leads if l["tier"] == 1]
    write_csv(OUTPUT_TIER1, tier1)

    # Tier 2 only
    tier2 = [l for l in leads if l["tier"] == 2]
    write_csv(OUTPUT_TIER2, tier2)

    print("\n--- TOP 10 LEADS (Tier 1, by reviews) ---")
    for i, lead in enumerate(tier1[:10], 1):
        print(f"{i}. {lead['title']}")
        print(f"   Phone: {lead['phone']} | Rating: {lead['review_rating']}⭐ ({lead['review_count']} reviews)")
        print(f"   Category: {lead['category']}")
        print(f"   Address: {lead['address']}")
        print(f"   Maps: {lead['google_maps_link']}")
        print()


if __name__ == "__main__":
    main()
