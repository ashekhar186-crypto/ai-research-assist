import os
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.connection import get_db
from app.models.paper import Paper
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _paper_dict(p: Paper) -> dict:
    """Serialize a Paper ORM object to the shape App.jsx expects."""
    analysis = {}
    if p.analysis_result:
        try:
            analysis = json.loads(p.analysis_result)
        except Exception:
            pass
    return {
        "id": p.id,
        "title": p.title or p.file_name or "Untitled",
        "authors": p.authors,
        "abstract": p.abstract,
        "file_name": p.file_name,
        "file_path": p.file_path,
        "file_size": p.file_size,
        "research_domain": p.research_domain or analysis.get("research_domain"),
        "processing_status": p.processing_status,   # App.jsx uses this field name
        "owner_id": p.owner_id,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


async def _run_analysis(paper_id: int, file_path: str, paper_title: str):
    """Background task: call AgentController, store results, update status."""
    from app.database.connection import AsyncSessionLocal
    from app.agents.controller import AgentController

    async with AsyncSessionLocal() as db:
        try:
            result_q = await db.execute(select(Paper).filter(Paper.id == paper_id))
            paper = result_q.scalars().first()
            if not paper:
                return

            paper.processing_status = "processing"
            await db.commit()

            agent = AgentController()
            result = await agent.analyze_paper(file_path, str(paper_id), paper_title)

            if "error" in result and not result.get("summary"):
                paper.processing_status = "failed"
            else:
                summary = result.get("summary", {})
                paper.processing_status = "complete"
                paper.analysis_result = json.dumps(summary)
                # Update denormalised columns for fast listing
                if summary.get("title"):
                    paper.title = summary["title"]
                if summary.get("authors"):
                    paper.authors = summary["authors"]
                if summary.get("research_domain"):
                    paper.research_domain = summary["research_domain"]

            await db.commit()

        except Exception as e:
            try:
                result_q = await db.execute(select(Paper).filter(Paper.id == paper_id))
                paper = result_q.scalars().first()
                if paper:
                    paper.processing_status = "failed"
                    await db.commit()
            except Exception:
                pass


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_papers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Paper)
        .filter(Paper.owner_id == current_user.id)
        .order_by(Paper.created_at.desc())
    )
    papers = result.scalars().all()
    return [_paper_dict(p) for p in papers]


@router.post("/upload")
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    # Create DB record first to get the auto-generated ID
    db_paper = Paper(
        title=file.filename,
        file_name=file.filename,
        file_size=len(content),
        processing_status="pending",
        owner_id=current_user.id,
    )
    db.add(db_paper)
    await db.commit()
    await db.refresh(db_paper)

    # Save file to disk using paper ID
    file_path = os.path.join(settings.UPLOAD_DIR, f"{db_paper.id}.pdf")
    with open(file_path, "wb") as f:
        f.write(content)

    db_paper.file_path = file_path
    await db.commit()

    # Kick off background analysis (non-blocking)
    background_tasks.add_task(_run_analysis, db_paper.id, file_path, file.filename)

    return _paper_dict(db_paper)


@router.get("/{paper_id}")
async def get_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id)
    )
    paper = result.scalars().first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return _paper_dict(paper)


@router.get("/{paper_id}/analysis")
async def get_paper_analysis(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Frontend polls this endpoint until status == 'complete'."""
    result = await db.execute(
        select(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id)
    )
    paper = result.scalars().first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    analysis = {}
    if paper.analysis_result:
        try:
            analysis = json.loads(paper.analysis_result)
        except Exception:
            pass

    return {
        "id": paper_id,
        "status": paper.processing_status,
        "analysis": analysis,
    }


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id)
    )
    paper = result.scalars().first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if paper.file_path and os.path.exists(paper.file_path):
        try:
            os.remove(paper.file_path)
        except OSError:
            pass

    await db.delete(paper)
    await db.commit()
    return {"message": "Paper deleted successfully"}


@router.post("/{paper_id}/reanalyze")
async def reanalyze_paper(
    paper_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Paper).filter(Paper.id == paper_id, Paper.owner_id == current_user.id)
    )
    paper = result.scalars().first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if not paper.file_path or not os.path.exists(paper.file_path):
        raise HTTPException(status_code=400, detail="Paper file not found — cannot reanalyze")

    paper.processing_status = "pending"
    paper.analysis_result = None
    await db.commit()

    background_tasks.add_task(_run_analysis, paper.id, paper.file_path, paper.file_name or "")
    return {"message": "Reanalysis started", "paper_id": paper_id}
