import json
from typing import List, Optional, Any, Union
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, field_validator

from app.database.connection import get_db
from app.models.user import User
from app.models.paper import Paper
from app.api.v1.auth import get_current_user
from app.agents.controller import AgentController

router = APIRouter()


# ── Request Models ─────────────────────────────────────────────────────────────

class LiteratureReviewRequest(BaseModel):
    topic: str
    paper_ids: List[Any] = []   # App.jsx sends integer IDs
    search_web: bool = False


class ResearchGapsRequest(BaseModel):
    topic: str
    paper_ids: List[Any] = []   # App.jsx sends integer IDs


class GrantProposalRequest(BaseModel):
    # App.jsx sends: topic, agency, budget, timeline, objectives
    topic: str
    agency: str = ""
    budget: str = ""
    timeline: str = ""
    objectives: List[Any] = []


class WritePaperRequest(BaseModel):
    topic: str
    target_journal: Optional[str] = ""
    word_count: Optional[str] = "5000"
    research_field: Optional[str] = "computer_science"
    paper_ids: List[Any] = []   # App.jsx sends integer IDs
    extra_context: Optional[dict] = {}


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/literature-review")
async def literature_review(
    request: LiteratureReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = AgentController()
    result = await agent.generate_literature_review(
        topic=request.topic,
        paper_ids=list(request.paper_ids),
        search_web=request.search_web,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/research-gaps")
async def research_gaps(
    request: ResearchGapsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = AgentController()
    result = await agent.identify_research_gaps(
        paper_ids=list(request.paper_ids),
        topic=request.topic,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/grant-proposal")
async def grant_proposal(
    request: GrantProposalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = AgentController()
    result = await agent.generate_grant_proposal(
        topic=request.topic,
        objectives=request.objectives,
        budget=request.budget,
        timeline=request.timeline,
        agency=request.agency,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/write-paper")
async def write_paper(
    request: WritePaperRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    extra_context = dict(request.extra_context or {})

    # ── Inject uploaded paper analyses into generation context ─────────────────
    # When the user selects uploaded papers in Step 6, their AI-extracted
    # summaries are fetched from the DB and injected into the generation context.
    # This allows all 6 calls to cite, reference, and build upon the user's
    # own uploaded literature — not just the AI's training knowledge.
    if request.paper_ids:
        paper_result = await db.execute(
            select(Paper).filter(
                Paper.id.in_(request.paper_ids),
                Paper.owner_id == current_user.id,
                Paper.processing_status == "complete",
            )
        )
        uploaded_papers = paper_result.scalars().all()

        if uploaded_papers:
            summaries = []
            for p in uploaded_papers:
                analysis = {}
                if p.analysis_result:
                    try:
                        analysis = json.loads(p.analysis_result)
                    except Exception:
                        pass
                # Include the most citation-useful fields from the AI analysis
                summaries.append({
                    "title":             p.title or analysis.get("title", "Untitled"),
                    "authors":           p.authors or analysis.get("authors", ""),
                    "year":              analysis.get("year", ""),
                    "venue":             analysis.get("publication_venue", ""),
                    "abstract_summary":  analysis.get("abstract_summary", p.abstract or ""),
                    "key_contributions": analysis.get("key_contributions", []),
                    "methodology":       analysis.get("methodology_summary", ""),
                    "main_results":      analysis.get("main_results", ""),
                    "datasets":          analysis.get("datasets_used", []),
                    "metrics":           analysis.get("evaluation_metrics", []),
                    "citation_context":  analysis.get("citation_context", ""),
                    "performance":       analysis.get("performance_metrics", ""),
                    "limitations":       analysis.get("limitations", ""),
                })

            # Compact JSON, capped at 6000 chars to stay within context budget
            uploaded_ctx = json.dumps(summaries, indent=2)[:6000]
            extra_context["_uploaded_papers"] = uploaded_ctx

    agent = AgentController()
    result = await agent.write_paper(
        topic=request.topic,
        target_journal=request.target_journal or "",
        word_count=request.word_count or "5000",
        research_field=request.research_field or "computer_science",
        paper_ids=list(request.paper_ids),
        extra_context=extra_context,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"paper": result}
