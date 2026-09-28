"""
AI Critic Agent — FastAPI Evaluation Service
Deployed on AWS Lambda via Mangum adapter for sub-500ms response time
"""

import os
import sys

# ===== MAC M4 PROTECTION =====
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from common.schemas import CriticResponse, EvaluationConfig
from common.database import DatabaseManager, EvaluationRecord
from reasoning.critic_agent import CriticAgent


# ============================================================
# App setup
# ============================================================

app = FastAPI(
    title="AI Critic Agent",
    description=(
        "LLM-driven venture evaluation service. "
        "Evaluates startup ideas by decomposing proposals and validating against "
        "historical failure patterns across risk dimensions."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ============================================================
# Request / Response models
# ============================================================

class CritiqueRequest(BaseModel):
    idea: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Startup idea in natural language",
        example="A social network for dog owners to arrange playdates in their neighborhood",
    )
    config: Optional[EvaluationConfig] = Field(
        default=None,
        description="Optional evaluation configuration (model, thresholds, categories)",
    )


class EvaluationSummary(BaseModel):
    evaluation_id: int
    idea: str
    idea_summary: str
    overall_risk: str
    success_probability: str
    created_at: str


class EvaluationDetail(EvaluationSummary):
    critique: CriticResponse


class StatsResponse(BaseModel):
    total_evaluations: int
    by_risk_level: dict


# ============================================================
# Lazy singletons (cold-start friendly for Lambda)
# ============================================================

_agent: Optional[CriticAgent] = None
_db: Optional[DatabaseManager] = None


def get_agent(config: Optional[EvaluationConfig] = None) -> CriticAgent:
    global _agent
    if _agent is None:
        _agent = CriticAgent(config=config)
    return _agent


def get_db() -> DatabaseManager:
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db


def _record_to_summary(record: EvaluationRecord) -> EvaluationSummary:
    return EvaluationSummary(
        evaluation_id=record.id,
        idea=record.idea,
        idea_summary=record.idea_summary or "",
        overall_risk=record.overall_risk,
        success_probability=record.success_probability,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


# ============================================================
# Endpoints
# ============================================================

@app.get("/health", tags=["System"])
def health_check():
    """Liveness probe for load balancer / Lambda health checks."""
    return {"status": "ok", "service": "ai-critic-agent", "version": "1.0.0"}


@app.post("/api/v1/critique", response_model=EvaluationDetail, tags=["Evaluation"])
def critique_idea(request: CritiqueRequest):
    """
    Submit a startup idea for multi-stage LLM critique.

    Runs decomposition → RAG retrieval → per-assumption critique → verdict synthesis.
    Results are persisted to PostgreSQL for historical analysis.
    """
    try:
        agent = get_agent(request.config)
        response: CriticResponse = agent.critique_idea(request.idea, config=request.config)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Critique failed: {e}")

    # Persist to database
    try:
        db = get_db()
        record = db.save_evaluation(request.idea, response)
        evaluation_id = record.id
        created_at = record.created_at.isoformat() if record.created_at else datetime.utcnow().isoformat()
    except Exception:
        # DB write failure is non-fatal — return result without persistence
        evaluation_id = -1
        created_at = datetime.utcnow().isoformat()

    return EvaluationDetail(
        evaluation_id=evaluation_id,
        idea=request.idea,
        idea_summary=response.idea_summary,
        overall_risk=response.verdict.overall_risk.value,
        success_probability=response.verdict.success_probability.value,
        created_at=created_at,
        critique=response,
    )


@app.get("/api/v1/evaluations/{evaluation_id}", response_model=EvaluationDetail, tags=["History"])
def get_evaluation(evaluation_id: int):
    """Retrieve a specific evaluation by ID."""
    db = get_db()
    record = db.get_evaluation(evaluation_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evaluation {evaluation_id} not found")

    critique = CriticResponse(**record.response_json)
    summary = _record_to_summary(record)
    return EvaluationDetail(**summary.model_dump(), critique=critique)


@app.get("/api/v1/evaluations", response_model=List[EvaluationSummary], tags=["History"])
def list_evaluations(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    risk_filter: Optional[str] = Query(
        default=None,
        description="Filter by risk level: low | medium | high | critical",
    ),
):
    """
    List past evaluations ordered by creation time (newest first).

    Supports pagination and risk-level filtering via indexed PostgreSQL queries.
    """
    db = get_db()
    records = db.list_evaluations(limit=limit, offset=offset, risk_filter=risk_filter)
    return [_record_to_summary(r) for r in records]


@app.get("/api/v1/stats", response_model=StatsResponse, tags=["History"])
def get_stats():
    """Aggregate statistics across all stored evaluations."""
    db = get_db()
    stats = db.get_stats()
    return StatsResponse(**stats)


# ============================================================
# AWS Lambda entrypoint (Mangum adapter)
# ============================================================

try:
    from mangum import Mangum
    lambda_handler = Mangum(app)
except ImportError:
    # Mangum not required for local development
    lambda_handler = None


# ============================================================
# Local dev server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
