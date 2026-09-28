"""
PostgreSQL Database Layer
Stores evaluation results with indexed queries for historical analysis
"""

import os
import datetime
from typing import Optional, List

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, JSON, DateTime, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


class EvaluationRecord(Base):
    """
    Persisted evaluation result

    Indexed on overall_risk and created_at for efficient historical queries.
    """
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    idea = Column(Text, nullable=False)
    idea_summary = Column(String(500))
    overall_risk = Column(String(50), nullable=False)
    success_probability = Column(String(50), nullable=False)
    response_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_evaluations_overall_risk", "overall_risk"),
        Index("ix_evaluations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationRecord id={self.id} risk={self.overall_risk} "
            f"created_at={self.created_at}>"
        )


class DatabaseManager:
    """
    SQLAlchemy-backed persistence layer for evaluation results

    Defaults to PostgreSQL. Set DATABASE_URL env var to override.
    Falls back to SQLite when DATABASE_URL is not set (useful for local dev).
    """

    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")

        if database_url is None:
            # Local dev fallback — SQLite keeps the same schema
            database_url = "sqlite:///./evaluations.db"

        # PostgreSQL needs pool_pre_ping to handle dropped connections on Lambda
        connect_args = {}
        if database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save_evaluation(self, idea: str, response) -> EvaluationRecord:
        """
        Persist a CriticResponse to the database.

        Args:
            idea: Original startup idea text
            response: CriticResponse Pydantic model

        Returns:
            EvaluationRecord with auto-assigned id and created_at
        """
        record = EvaluationRecord(
            idea=idea,
            idea_summary=response.idea_summary,
            overall_risk=response.verdict.overall_risk.value,
            success_probability=response.verdict.success_probability.value,
            response_json=response.model_dump(),
        )
        with self.SessionLocal() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def get_evaluation(self, evaluation_id: int) -> Optional[EvaluationRecord]:
        """Retrieve a single evaluation by primary key."""
        with self.SessionLocal() as session:
            return (
                session.query(EvaluationRecord)
                .filter(EvaluationRecord.id == evaluation_id)
                .first()
            )

    def list_evaluations(
        self,
        limit: int = 10,
        offset: int = 0,
        risk_filter: Optional[str] = None,
    ) -> List[EvaluationRecord]:
        """
        List evaluations ordered by creation time (newest first).

        Args:
            limit: Max rows to return
            offset: Rows to skip (for pagination)
            risk_filter: Filter by overall_risk value (uses indexed column)

        Returns:
            List of EvaluationRecord objects
        """
        with self.SessionLocal() as session:
            query = session.query(EvaluationRecord)
            if risk_filter:
                query = query.filter(EvaluationRecord.overall_risk == risk_filter)
            return (
                query.order_by(EvaluationRecord.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    def get_stats(self) -> dict:
        """Aggregate statistics for reporting."""
        with self.SessionLocal() as session:
            total = session.query(EvaluationRecord).count()
            risk_counts: dict = {}
            for record in session.query(EvaluationRecord).all():
                risk_counts[record.overall_risk] = (
                    risk_counts.get(record.overall_risk, 0) + 1
                )
            return {"total_evaluations": total, "by_risk_level": risk_counts}
