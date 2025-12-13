"""
AI Critic Agent - System Constants
Configuration values and validation constraints
"""

from typing import List
from common.schemas import (
    RiskCategory, 
    RiskLevel, 
    ImportanceLevel, 
    SuccessProbability
)


# ============================================================
# Enum Value Lists (for validation and iteration)
# ============================================================

RISK_CATEGORIES: List[str] = [
    RiskCategory.MARKET.value,
    RiskCategory.COMPETITION.value,
    RiskCategory.EXECUTION.value,
    RiskCategory.MONETIZATION.value,
    RiskCategory.USER_BEHAVIOR.value,
    RiskCategory.TIMING.value,
]

RISK_LEVELS: List[str] = [
    RiskLevel.LOW.value,
    RiskLevel.MEDIUM.value,
    RiskLevel.HIGH.value,
    RiskLevel.CRITICAL.value,
]

IMPORTANCE_LEVELS: List[str] = [
    ImportanceLevel.CRITICAL.value,
    ImportanceLevel.IMPORTANT.value,
    ImportanceLevel.MINOR.value,
]

SUCCESS_PROBABILITIES: List[str] = [
    SuccessProbability.VERY_LOW.value,
    SuccessProbability.LOW.value,
    SuccessProbability.MODERATE.value,
]


# ============================================================
# Knowledge Base Categories
# ============================================================

# These correspond to knowledge_base/data/ folder structure
EVIDENCE_CATEGORIES: List[str] = [
    "market",        # Market-related failures and data
    "competition",   # Competitive landscape cases
    "execution",     # Execution and operational failures
    "failures",      # General startup failure case studies
]


# ============================================================
# System Limits and Constraints
# ============================================================

# Input validation
MIN_IDEA_LENGTH: int = 10          # Minimum characters for user idea
MAX_IDEA_LENGTH: int = 1000        # Maximum characters for user idea

# Decomposer constraints
MAX_ASSUMPTIONS: int = 15          # Maximum number of assumptions per idea
MIN_ASSUMPTIONS: int = 3           # Minimum number of assumptions per idea

# Knowledge base retrieval
DEFAULT_EVIDENCE_COUNT: int = 5    # Default number of evidence items to retrieve
MAX_EVIDENCE_COUNT: int = 10       # Maximum evidence items per query
MIN_RELEVANCE_SCORE: float = 0.3   # Minimum relevance score to include evidence

# Output formatting
CRITIQUE_MIN_LENGTH: int = 100     # Minimum characters for each critique
SUMMARY_MIN_LENGTH: int = 150      # Minimum characters for final summary
MAX_KEY_CONCERNS: int = 5          # Maximum key concerns in verdict


# ============================================================
# Prompt Template Paths
# ============================================================

PROMPT_DIR: str = "prompts/"
SYSTEM_PROMPT_PATH: str = f"{PROMPT_DIR}system.txt"
CRITIQUE_PROMPT_PATH: str = f"{PROMPT_DIR}critique.txt"
SUMMARY_PROMPT_PATH: str = f"{PROMPT_DIR}summary.txt"
DECOMPOSE_PROMPT_PATH: str = "idea_decomposer/prompts/idea_decompose.txt"


# ============================================================
# Knowledge Base Configuration
# ============================================================

KNOWLEDGE_BASE_DIR: str = "knowledge_base/data/"
VECTOR_DB_PATH: str = "knowledge_base/vector_store/"
EMBEDDING_MODEL: str = "text-embedding-ada-002"  # or your chosen model


# ============================================================
# Risk Severity Mapping (for scoring logic)
# ============================================================

RISK_LEVEL_SCORES = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}

IMPORTANCE_SCORES = {
    ImportanceLevel.MINOR: 1,
    ImportanceLevel.IMPORTANT: 2,
    ImportanceLevel.CRITICAL: 3,
}


# ============================================================
# Helper Functions
# ============================================================

def get_overall_risk_from_critiques(critiques: list) -> RiskLevel:
    """
    Calculate overall risk level from multiple critiques
    
    Args:
        critiques: List of Critique objects
        
    Returns:
        Overall RiskLevel enum value
    """
    if not critiques:
        return RiskLevel.MEDIUM
    
    # Calculate average risk score
    total_score = sum(RISK_LEVEL_SCORES[c.risk_level] for c in critiques)
    avg_score = total_score / len(critiques)
    
    # Map back to risk level
    if avg_score >= 3.5:
        return RiskLevel.CRITICAL
    elif avg_score >= 2.5:
        return RiskLevel.HIGH
    elif avg_score >= 1.5:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


def validate_evidence_category(category: str) -> bool:
    """
    Check if a category is valid for knowledge base
    
    Args:
        category: Category string to validate
        
    Returns:
        True if valid, False otherwise
    """
    return category in EVIDENCE_CATEGORIES or category in RISK_CATEGORIES