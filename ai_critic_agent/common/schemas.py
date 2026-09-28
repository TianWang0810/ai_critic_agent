"""
AI Critic Agent - Core Data Structures
Interface contracts between all modules
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from enum import Enum


# ============================================================
# Enum Type Definitions
# ============================================================

class RiskCategory(str, Enum):
    """Risk category for startup assumptions"""
    MARKET = "market"
    EXECUTION = "execution"
    COMPETITION = "competition"
    MONETIZATION = "monetization"
    USER_BEHAVIOR = "user_behavior"
    TIMING = "timing"
    GENERAL = "general"  # General/综合失败案例


class ImportanceLevel(str, Enum):
    """Importance level of an assumption for startup success"""
    CRITICAL = "critical"
    IMPORTANT = "important"
    MINOR = "minor"


class RiskLevel(str, Enum):
    """Risk severity level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SuccessProbability(str, Enum):
    """Estimated probability of startup success"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"


# ============================================================
# Module 1: Idea Decomposer Output
# ============================================================

class StartupAssumption(BaseModel):
    """
    A single startup assumption
    
    Represents one condition that must be true for the startup to succeed.
    """
    id: str = Field(description="Unique identifier, e.g., 'assumption_1'")
    category: RiskCategory = Field(description="Risk category of this assumption")
    assumption: str = Field(description="Assumption statement in declarative form")
    importance: ImportanceLevel = Field(description="Importance for success")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "assumption_1",
                "category": "market",
                "assumption": "College students will pay $20/month for AI tutoring",
                "importance": "critical"
            }
        }


class DecomposedIdea(BaseModel):
    """
    Decomposed startup idea with structured assumptions
    
    Output of the Idea Decomposer module.
    """
    original_idea: str = Field(description="User's original idea text (raw input)")
    product_type: str = Field(description="Product category, e.g., 'SaaS', 'marketplace', 'consumer app'")
    target_user: str = Field(description="Specific target user segment")
    value_proposition: str = Field(description="Core value proposition in one sentence")
    assumptions: List[StartupAssumption] = Field(description="List of all critical assumptions")
    risk_categories: List[RiskCategory] = Field(description="Risk categories identified in this idea")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_idea": "An AI tutor app for college students to help with homework",
                "product_type": "SaaS",
                "target_user": "US college undergraduate students",
                "value_proposition": "24/7 personalized AI learning assistant for homework help",
                "assumptions": [],
                "risk_categories": ["market", "competition", "execution"]
            }
        }


# ============================================================
# Module 2: Knowledge Base Output
# ============================================================

class EvidenceItem(BaseModel):
    """
    A single piece of counter-evidence
    
    Retrieved from the knowledge base to support critical arguments.
    """
    source: str = Field(description="Source identifier, e.g., filename or case study name")
    content: str = Field(description="Evidence content text")
    relevance_score: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Relevance score to the query (0.0-1.0)"
    )
    category: RiskCategory = Field(description="Evidence category")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "quibi_failure_2020.md",
                "content": "Quibi raised $1.8B but failed within 6 months due to poor product-market fit...",
                "relevance_score": 0.87,
                "category": "market"
            }
        }


class RetrievalResult(BaseModel):
    """
    Knowledge base retrieval result
    
    All relevant evidence for a given assumption query.
    """
    query: str = Field(description="The assumption text that was queried")
    evidence: List[EvidenceItem] = Field(description="Retrieved evidence items, sorted by relevance")
    total_retrieved: int = Field(description="Total number of evidence items retrieved", default=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "College students will pay for AI tutoring",
                "evidence": [],
                "total_retrieved": 3
            }
        }


# ============================================================
# Module 3: Reasoning & Structured Output
# ============================================================

class Critique(BaseModel):
    """
    Critique of a single assumption
    
    Contains counter-argument, evidence, and risk assessment.
    """
    assumption_id: str = Field(description="ID of the assumption being critiqued")
    assumption_text: str = Field(description="Original assumption text")
    counterargument: str = Field(description="Critical argument explaining why this assumption is risky")
    evidence_used: List[str] = Field(description="List of evidence sources used")
    risk_level: RiskLevel = Field(description="Assessed risk level for this assumption")
    
    class Config:
        json_schema_extra = {
            "example": {
                "assumption_id": "assumption_1",
                "assumption_text": "College students will pay $20/month for AI tutoring",
                "counterargument": "Historical data shows college students have low willingness to pay for subscription services beyond streaming...",
                "evidence_used": ["chegg_pricing_study.md", "student_spending_2023.md"],
                "risk_level": "high"
            }
        }


class FinalVerdict(BaseModel):
    """
    Final overall assessment
    
    Synthesized judgment based on all critiques.
    """
    overall_risk: RiskLevel = Field(description="Overall risk level")
    key_concerns: List[str] = Field(
        description="Top 3-5 critical concerns",
        max_length=5
    )
    success_probability: SuccessProbability = Field(description="Estimated probability of success")
    summary: str = Field(description="One paragraph summary (3-5 sentences)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_risk": "high",
                "key_concerns": [
                    "Insufficient student willingness to pay",
                    "Difficult to differentiate from ChatGPT",
                    "Quality assurance challenges in education"
                ],
                "success_probability": "low",
                "summary": "This idea faces severe market and competitive risks. The target demographic has historically shown low subscription adoption..."
            }
        }


class CriticResponse(BaseModel):
    """
    Complete critic output
    
    Final structured output of the entire system.
    This is what the API returns to the user.
    """
    idea_summary: str = Field(description="Brief summary of the startup idea")
    critiques: List[Critique] = Field(description="List of all assumption critiques")
    verdict: FinalVerdict = Field(description="Final overall verdict")
    
    class Config:
        json_schema_extra = {
            "example": {
                "idea_summary": "24/7 AI learning assistant for college students",
                "critiques": [],
                "verdict": {}
            }
        }


# ============================================================
# System Input (User-facing)
# ============================================================

class UserInput(BaseModel):
    """
    User's input to the system

    Single startup idea as plain text.
    """
    idea: str = Field(
        description="User's startup idea in natural language",
        min_length=10,
        max_length=1000
    )

    class Config:
        json_schema_extra = {
            "example": {
                "idea": "A social network for dog owners to arrange playdates in their neighborhood"
            }
        }


class EvaluationConfig(BaseModel):
    """
    Configurable evaluation harness settings

    Controls critique criteria, model selection, and evaluation workflow.
    """
    model_name: str = Field(
        default="gpt-4o",
        description="OpenAI model to use for evaluation"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="LLM temperature for critique generation"
    )
    focus_categories: Optional[List[RiskCategory]] = Field(
        default=None,
        description="Risk categories to prioritize. If None, all categories are evaluated."
    )
    evidence_count: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of evidence items to retrieve per assumption"
    )
    max_assumptions: int = Field(
        default=8,
        ge=3,
        le=15,
        description="Maximum number of assumptions to critique"
    )
    min_risk_threshold: RiskLevel = Field(
        default=RiskLevel.LOW,
        description="Only report critiques at or above this risk level"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "gpt-4o",
                "temperature": 0.7,
                "focus_categories": ["market", "competition"],
                "evidence_count": 5,
                "max_assumptions": 8,
                "min_risk_threshold": "medium"
            }
        }