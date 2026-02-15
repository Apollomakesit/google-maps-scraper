"""API routes for lead management (Phase 1)."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.database import get_supabase
from app.models import (
    LeadListResponse,
    LeadResponse,
    LeadUpdateRequest,
    NicheType,
    ScrapeJobResponse,
    ScrapeRequest,
    StatsResponse,
    NICHE_LABELS_RO,
    NICHE_SEARCH_QUERIES,
)
from app.services.lead_scraper import process_scrape_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])


# ============================================================================
# IMPORTANT: Route ordering matters in FastAPI.
# Specific named routes (e.g. /stats, /scrape, /niches/list)
# MUST be defined BEFORE the catch-all /{lead_id} routes.
# Otherwise FastAPI treats "stats", "scrape", etc. as a lead_id.
# ============================================================================


@router.get("", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=5, le=100),
    niche: Optional[NicheType] = None,
    tier: Optional[int] = Query(default=None, ge=1, le=3),
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="review_count", pattern="^(review_count|review_rating|created_at|name|tier)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    city: Optional[str] = None,
):
    """List leads with filtering, pagination, and sorting."""
    db = get_supabase()

    try:
        # Build query
        query = db.table("leads").select("*", count="exact")

        if niche:
            query = query.eq("niche", niche.value)
        if tier:
            query = query.eq("tier", tier)
        if status:
            query = query.eq("status", status)
        if city:
            query = query.ilike("city", f"%{city}%")
        if search:
            query = query.or_(
                f"name.ilike.%{search}%,address.ilike.%{search}%,phone.ilike.%{search}%"
            )

        # Sorting
        query = query.order(sort_by, desc=(sort_order == "desc"))

        # Pagination
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)

        result = query.execute()

        total = result.count or 0
        total_pages = max(1, (total + per_page - 1) // per_page)

        leads = []
        for row in result.data or []:
            leads.append(LeadResponse(
                id=row["id"],
                name=row.get("name", ""),
                google_maps_link=row.get("google_maps_link"),
                place_id=row.get("place_id"),
                niche=row.get("niche", "other"),
                categories=row.get("categories") or [],
                tier=row.get("tier", 3),
                phone=row.get("phone"),
                emails=row.get("emails") or [],
                address=row.get("address"),
                city=row.get("city", ""),
                borough=row.get("borough"),
                latitude=row.get("latitude"),
                longitude=row.get("longitude"),
                review_count=row.get("review_count", 0),
                review_rating=float(row.get("review_rating", 0)),
                website_url=row.get("website_url"),
                website_status=row.get("website_status", "missing"),
                status=row.get("status", "new"),
                notes=row.get("notes"),
                scraped_at=row.get("scraped_at"),
                created_at=row.get("created_at"),
            ))

        return LeadListResponse(
            leads=leads,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la încărcarea lead-urilor: {str(e)}")


# ── Named routes FIRST (before /{lead_id}) ──────────────────────────────────


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics."""
    db = get_supabase()

    try:
        # Total leads
        total_result = db.table("leads").select("id", count="exact").execute()
        total_leads = total_result.count or 0

        # New leads
        new_result = db.table("leads").select("id", count="exact").eq("status", "new").execute()
        new_leads = new_result.count or 0

        # Analyzed leads
        analyzed_result = db.table("leads").select("id", count="exact").eq("status", "analyzed").execute()
        analyzed_leads = analyzed_result.count or 0

        # Total analyses
        analyses_result = (
            db.table("market_intelligence")
            .select("id", count="exact")
            .eq("analysis_status", "completed")
            .execute()
        )
        total_analyses = analyses_result.count or 0

        # Leads by niche
        all_leads = db.table("leads").select("niche, tier, review_rating").execute()
        niche_counts: dict[str, int] = {}
        tier_counts: dict[str, int] = {}
        total_rating = 0.0
        rating_count = 0

        for row in all_leads.data or []:
            niche = row.get("niche", "other")
            niche_label = NICHE_LABELS_RO.get(niche, niche)
            niche_counts[niche_label] = niche_counts.get(niche_label, 0) + 1

            tier = str(row.get("tier", 3))
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

            rating = float(row.get("review_rating", 0))
            if rating > 0:
                total_rating += rating
                rating_count += 1

        avg_rating = round(total_rating / rating_count, 1) if rating_count > 0 else 0.0

        return StatsResponse(
            total_leads=total_leads,
            new_leads=new_leads,
            analyzed_leads=analyzed_leads,
            total_analyses=total_analyses,
            leads_by_niche=niche_counts,
            leads_by_tier=tier_counts,
            avg_rating=avg_rating,
        )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare statistici: {str(e)}")


@router.post("/scrape", response_model=ScrapeJobResponse)
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Start a new scraping job (Phase 1 pipeline)."""
    db = get_supabase()

    try:
        # Build search query
        queries = NICHE_SEARCH_QUERIES.get(request.niche.value, [request.niche.value])
        query_text = f"{queries[0]} in {request.location}" if queries else f"{request.niche.value} in {request.location}"

        # Create job record
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "location": request.location,
            "niche": request.niche.value,
            "query": query_text,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        db.table("scrape_jobs").insert(job_data).execute()

        # Run scraping in background
        background_tasks.add_task(
            process_scrape_job,
            job_id=job_id,
            location=request.location,
            niche=request.niche,
            max_results=request.max_results,
        )

        return ScrapeJobResponse(
            id=job_id,
            location=request.location,
            niche=request.niche.value,
            query=query_text,
            status="queued",
            created_at=job_data["created_at"],
        )

    except Exception as e:
        logger.error(f"Error starting scrape: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la pornirea scraping-ului: {str(e)}")


@router.get("/niches/list")
async def list_niches():
    """List all available niches with Romanian labels."""
    return {
        "niches": [
            {"value": niche.value, "label": NICHE_LABELS_RO.get(niche.value, niche.value)}
            for niche in NicheType
        ]
    }


@router.get("/jobs/{job_id}", response_model=ScrapeJobResponse)
async def get_scrape_job(job_id: str):
    """Get the status of a scraping job."""
    db = get_supabase()

    try:
        result = db.table("scrape_jobs").select("*").eq("id", job_id).single().execute()
        row = result.data

        if not row:
            raise HTTPException(status_code=404, detail="Job-ul nu a fost găsit")

        return ScrapeJobResponse(
            id=row["id"],
            location=row.get("location", ""),
            niche=row.get("niche", ""),
            query=row.get("query", ""),
            status=row.get("status", ""),
            total_results=row.get("total_results", 0),
            filtered_leads=row.get("filtered_leads", 0),
            error_message=row.get("error_message"),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            created_at=row.get("created_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Catch-all /{lead_id} routes LAST ────────────────────────────────────────
# These MUST be after all named routes to avoid path conflicts.


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str):
    """Get a single lead by ID."""
    db = get_supabase()

    try:
        result = db.table("leads").select("*").eq("id", lead_id).single().execute()
        row = result.data

        if not row:
            raise HTTPException(status_code=404, detail="Lead-ul nu a fost găsit")

        return LeadResponse(
            id=row["id"],
            name=row.get("name", ""),
            google_maps_link=row.get("google_maps_link"),
            place_id=row.get("place_id"),
            niche=row.get("niche", "other"),
            categories=row.get("categories") or [],
            tier=row.get("tier", 3),
            phone=row.get("phone"),
            emails=row.get("emails") or [],
            address=row.get("address"),
            city=row.get("city", ""),
            borough=row.get("borough"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            review_count=row.get("review_count", 0),
            review_rating=float(row.get("review_rating", 0)),
            website_url=row.get("website_url"),
            website_status=row.get("website_status", "missing"),
            status=row.get("status", "new"),
            notes=row.get("notes"),
            scraped_at=row.get("scraped_at"),
            created_at=row.get("created_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: str, update: LeadUpdateRequest):
    """Update a lead's status or notes."""
    db = get_supabase()

    try:
        update_data = {}
        if update.status is not None:
            update_data["status"] = update.status.value
        if update.notes is not None:
            update_data["notes"] = update.notes

        if not update_data:
            raise HTTPException(status_code=400, detail="Nicio modificare specificată")

        result = db.table("leads").update(update_data).eq("id", lead_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Lead-ul nu a fost găsit")

        return await get_lead(lead_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{lead_id}")
async def delete_lead(lead_id: str):
    """Delete a lead."""
    db = get_supabase()

    try:
        db.table("leads").delete().eq("id", lead_id).execute()
        return {"message": "Lead-ul a fost șters cu succes", "id": lead_id}

    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
