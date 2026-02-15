"""API routes for competitor analysis / market intelligence (Phase 2)."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.database import get_supabase
from app.models import (
    AnalyzeRequest,
    MarketIntelligenceResponse,
    CommonPatterns,
    CompetitorData,
    DesignTokens,
    WebsiteStructure,
    Copywriting,
)
from app.services.competitor_analyst import analyze_competitors_for_lead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.post("/analyze", response_model=MarketIntelligenceResponse)
async def start_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Start competitor analysis for a specific lead (Phase 2 pipeline).
    This creates a market_intelligence record and runs analysis in the background.
    """
    db = get_supabase()

    try:
        # Verify the lead exists
        lead_result = db.table("leads").select("*").eq("id", request.lead_id).single().execute()
        lead = lead_result.data

        if not lead:
            raise HTTPException(status_code=404, detail="Lead-ul nu a fost găsit")

        # Check if there's already an analysis in progress
        existing = (
            db.table("market_intelligence")
            .select("*")
            .eq("lead_id", request.lead_id)
            .in_("analysis_status", ["pending", "in_progress"])
            .execute()
        )

        if existing.data:
            # Return the existing analysis record
            row = existing.data[0]
            return _build_intelligence_response(row)

        # Create new market intelligence record
        intelligence_id = str(uuid.uuid4())
        intelligence_data = {
            "id": intelligence_id,
            "lead_id": request.lead_id,
            "niche": lead.get("niche", "other"),
            "location": lead.get("city", "București"),
            "analysis_status": "pending",
            "competitors": [],
            "common_patterns": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        db.table("market_intelligence").insert(intelligence_data).execute()

        # Run analysis in background
        background_tasks.add_task(
            analyze_competitors_for_lead,
            lead_id=request.lead_id,
            intelligence_id=intelligence_id,
            top_n=request.top_n,
        )

        return MarketIntelligenceResponse(
            id=intelligence_id,
            lead_id=request.lead_id,
            niche=lead.get("niche", "other"),
            location=lead.get("city", "București"),
            analysis_status="pending",
            competitors=[],
            common_patterns=CommonPatterns(),
            created_at=intelligence_data["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis for lead {request.lead_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Eroare la pornirea analizei: {str(e)}",
        )


@router.get("/lead/{lead_id}", response_model=Optional[MarketIntelligenceResponse])
async def get_intelligence_for_lead(lead_id: str):
    """Get the latest market intelligence for a specific lead."""
    db = get_supabase()

    try:
        result = (
            db.table("market_intelligence")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return _build_intelligence_response(result.data[0])

    except Exception as e:
        logger.error(f"Error getting intelligence for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{intelligence_id}", response_model=MarketIntelligenceResponse)
async def get_intelligence(intelligence_id: str):
    """Get a specific market intelligence record."""
    db = get_supabase()

    try:
        result = (
            db.table("market_intelligence")
            .select("*")
            .eq("id", intelligence_id)
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Analiza nu a fost găsită")

        return _build_intelligence_response(result.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting intelligence {intelligence_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[MarketIntelligenceResponse])
async def list_intelligence(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=5, le=50),
    status: Optional[str] = None,
):
    """List all market intelligence records."""
    db = get_supabase()

    try:
        query = db.table("market_intelligence").select("*")

        if status:
            query = query.eq("analysis_status", status)

        query = query.order("created_at", desc=True)

        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)

        result = query.execute()

        return [_build_intelligence_response(row) for row in result.data or []]

    except Exception as e:
        logger.error(f"Error listing intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{intelligence_id}")
async def delete_intelligence(intelligence_id: str):
    """Delete a market intelligence record."""
    db = get_supabase()

    try:
        db.table("market_intelligence").delete().eq("id", intelligence_id).execute()
        return {"message": "Analiza a fost ștearsă", "id": intelligence_id}

    except Exception as e:
        logger.error(f"Error deleting intelligence {intelligence_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_intelligence_response(row: dict) -> MarketIntelligenceResponse:
    """Build a MarketIntelligenceResponse from a database row."""
    competitors_data = row.get("competitors") or []
    competitors = []

    for comp in competitors_data:
        dt = comp.get("design_tokens", {})
        st = comp.get("structure", {})
        cw = comp.get("copywriting", {})

        competitors.append(CompetitorData(
            name=comp.get("name", ""),
            website_url=comp.get("website_url"),
            google_maps_link=comp.get("google_maps_link"),
            rating=float(comp.get("rating", 0)),
            review_count=comp.get("review_count", 0),
            rank=comp.get("rank", 0),
            design_tokens=DesignTokens(
                color_palette=dt.get("color_palette", []),
                dominant_color=dt.get("dominant_color"),
                font_families=dt.get("font_families", []),
            ),
            structure=WebsiteStructure(
                sections=st.get("sections", []),
                has_before_after=st.get("has_before_after", False),
                has_booking_form=st.get("has_booking_form", False),
                has_pricing=st.get("has_pricing", False),
                has_blog=st.get("has_blog", False),
                has_gallery=st.get("has_gallery", False),
                has_testimonials=st.get("has_testimonials", False),
                has_faq=st.get("has_faq", False),
                has_map=st.get("has_map", False),
            ),
            copywriting=Copywriting(
                h1_headline=cw.get("h1_headline"),
                h2_headlines=cw.get("h2_headlines", []),
                cta_buttons=cw.get("cta_buttons", []),
                value_propositions=cw.get("value_propositions", []),
                tone=cw.get("tone", "professional"),
            ),
            meta=comp.get("meta", {}),
        ))

    patterns_data = row.get("common_patterns") or {}
    common_patterns = CommonPatterns(
        dominant_colors=patterns_data.get("dominant_colors", []),
        common_sections=patterns_data.get("common_sections", []),
        common_cta_text=patterns_data.get("common_cta_text", []),
        messaging_themes=patterns_data.get("messaging_themes", []),
        recommended_structure=patterns_data.get("recommended_structure", []),
        summary_ro=patterns_data.get("summary_ro", ""),
    )

    return MarketIntelligenceResponse(
        id=row["id"],
        lead_id=row.get("lead_id", ""),
        niche=row.get("niche", "other"),
        location=row.get("location", ""),
        analysis_status=row.get("analysis_status", "pending"),
        competitors=competitors,
        common_patterns=common_patterns,
        strategy_summary=row.get("strategy_summary"),
        error_message=row.get("error_message"),
        analyzed_at=row.get("analyzed_at"),
        created_at=row.get("created_at"),
    )
