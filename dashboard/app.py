"""
dashboard/app.py - Phase 5: FastAPI Dashboard for AiPi-MemoryCore
Metrics API for Chart.js / ECharts / D3 frontend.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from sqlalchemy import func
from memory_core.models import (
    Conversation, Decision, OpenLoop, Pod, Project,
    get_engine, get_session
)

app    = FastAPI(title="AiPi-MemoryCore Dashboard", version="0.1.0")
engine = get_engine()


@app.get("/")
async def root():
    return {"status": "AiPi-MemoryCore running", "docs": "/docs"}


@app.get("/metrics/summary")
async def metrics_summary():
    """Gauge data: open loops, decisions, fragmentation index, completion ratio."""
    s = get_session(engine)
    try:
        total_convos    = s.query(func.count(Conversation.id)).scalar() or 0
        open_loops      = s.query(func.count(OpenLoop.id)).filter(OpenLoop.is_closed == False).scalar() or 0
        total_decisions = s.query(func.count(Decision.id)).scalar() or 0
        exec_decisions  = s.query(func.count(Decision.id)).filter(Decision.is_executed == True).scalar() or 0
        active_projects = s.query(func.count(Project.id)).filter(Project.status == "active").scalar() or 0
        stale_count     = s.query(func.count(Conversation.id)).filter(Conversation.is_stale == True).scalar() or 0
        pod_count       = s.query(func.count(Pod.id)).scalar() or 0
        completion      = round(exec_decisions / total_decisions, 3) if total_decisions else 0.0
        fragmentation   = round(pod_count / active_projects, 2)      if active_projects else float(pod_count)
        return {
            "total_conversations": total_convos,
            "open_loops_count":    open_loops,
            "total_decisions":     total_decisions,
            "executed_decisions":  exec_decisions,
            "completion_ratio":    completion,
            "active_projects":     active_projects,
            "stale_thread_count":  stale_count,
            "pod_count":           pod_count,
            "fragmentation_index": fragmentation,
        }
    finally:
        s.close()


@app.get("/metrics/open_loops")
async def get_open_loops(limit: int = 50):
    """Unfinished loop heatmap data."""
    s = get_session(engine)
    try:
        rows = s.query(OpenLoop).filter(OpenLoop.is_closed == False)\
                .order_by(OpenLoop.days_open.desc()).limit(limit).all()
        return [{"id": r.id, "text": r.text, "days_open": r.days_open,
                 "conversation_id": r.conversation_id} for r in rows]
    finally:
        s.close()


@app.get("/metrics/tech_stack")
async def tech_stack_frequency():
    """Word cloud source: tech keyword mention frequencies."""
    s = get_session(engine)
    try:
        freq: dict[str, int] = {}
        for (stack,) in s.query(Conversation.tech_stack).all():
            for tech in (stack or []):
                freq[tech] = freq.get(tech, 0) + 1
        return sorted([{"tech": k, "count": v} for k, v in freq.items()],
                      key=lambda x: x["count"], reverse=True)
    finally:
        s.close()


@app.get("/metrics/projects")
async def projects_activity():
    """Per-project activity and completion."""
    s = get_session(engine)
    try:
        return [{"id": p.id, "name": p.name, "category": p.category,
                 "status": p.status, "is_strategic": p.is_strategic,
                 "completion_ratio": p.completion_ratio, "pod_count": len(p.pods)}
                for p in s.query(Project).all()]
    finally:
        s.close()


@app.get("/metrics/emotional_volatility")
async def emotional_volatility():
    """Emotion marker frequencies for volatility gauge."""
    s = get_session(engine)
    try:
        freq: dict[str, int] = {}
        for (markers,) in s.query(Conversation.emotional_markers).all():
            for m in (markers or []):
                freq[m] = freq.get(m, 0) + 1
        return sorted([{"emotion": k, "count": v} for k, v in freq.items()],
                      key=lambda x: x["count"], reverse=True)
    finally:
        s.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8000, reload=True)
