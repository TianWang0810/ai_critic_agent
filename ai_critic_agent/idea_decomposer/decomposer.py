"""
Idea Decomposer Module
Breaks down user startup ideas into structured assumptions
Returns JSON format for easy integration with other modules
"""
import os
import json
from pathlib import Path
from typing import Optional, Union, Dict, List
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import ValidationError

from common.schemas import DecomposedIdea, UserInput, RiskCategory
from common.constants import (
    MIN_IDEA_LENGTH,
    MAX_IDEA_LENGTH,
    MIN_ASSUMPTIONS,
    MAX_ASSUMPTIONS,
)


class IdeaDecomposer:
    """
    Decomposes raw startup ideas into structured assumptions
    
    Uses LLM with Pydantic structured output to analyze and break down
    user's startup idea into testable assumptions.
    
    Returns JSON dict by default for easy integration with other modules.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        prompt_path: Optional[str] = None
    ):
        # Read model from env if not provided
        if model_name is None:
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o")

        # Initialize LLM (API key read from env)
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Structured output
        self.structured_llm = self.llm.with_structured_output(DecomposedIdea)

        # Load prompt
        if prompt_path is None:
            prompt_path = Path(__file__).parent / "prompts" / "idea_decompose.txt"

        self.prompt_template = self._load_prompt(prompt_path)

    def _load_prompt(self, path: Path) -> PromptTemplate:
        """Load prompt template from file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                template = f.read()
            return PromptTemplate(
                template=template,
                input_variables=["idea"],
                validate_template=True  # Validate template variables
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt template not found at {path}. "
                f"Please ensure idea_decompose.txt exists in idea_decomposer/prompts/"
            )
    
    def _validate_input(self, idea: str) -> None:
        """
        Validate user input
        
        Args:
            idea: User's startup idea text
            
        Raises:
            ValueError: If input is invalid
        """
        if not idea or not idea.strip():
            raise ValueError("Idea cannot be empty")
        
        if len(idea) < MIN_IDEA_LENGTH:
            raise ValueError(
                f"Idea too short. Minimum {MIN_IDEA_LENGTH} characters required."
            )
        
        if len(idea) > MAX_IDEA_LENGTH:
            raise ValueError(
                f"Idea too long. Maximum {MAX_IDEA_LENGTH} characters allowed."
            )
    
    def _normalize_value(self, value):
        """
        Normalize enum/string value to handle both Enum and str types
        
        Args:
            value: Either an Enum with .value or a string
            
        Returns:
            String value
        """
        return getattr(value, "value", value)
    
    def _validate_assumption_ids(self, decomposed: DecomposedIdea) -> None:
        """
        Validate assumption IDs follow the required format and are unique
        
        Args:
            decomposed: Parsed DecomposedIdea object
            
        Raises:
            ValueError: If IDs are invalid or duplicated
        """
        seen_ids = set()
        
        for i, assumption in enumerate(decomposed.assumptions, start=1):
            assumption_id = assumption.id
            
            # Check format: should be "assumption_N" where N is a number
            expected_id = f"assumption_{i}"
            if assumption_id != expected_id:
                # Auto-fix: regenerate correct IDs
                assumption.id = expected_id
                continue
            
            # Check for duplicates
            if assumption_id in seen_ids:
                raise ValueError(
                    f"Duplicate assumption ID found: {assumption_id}. "
                    f"All assumption IDs must be unique."
                )
            
            seen_ids.add(assumption_id)
    
    def _validate_risk_categories(self, decomposed: DecomposedIdea) -> None:
        """
        Validate risk_categories matches the categories in assumptions
        
        Args:
            decomposed: Parsed DecomposedIdea object
            
        Raises:
            ValueError: If risk_categories doesn't match assumptions
        """
        # Get unique categories from assumptions
        assumption_categories = sorted(set(
            self._normalize_value(a.category) for a in decomposed.assumptions
        ))
        
        # Get risk_categories from output
        risk_categories = sorted([
            self._normalize_value(cat) for cat in decomposed.risk_categories
        ])
        
        # Auto-correct if mismatch
        if assumption_categories != risk_categories:
            # Update risk_categories to match assumptions
            decomposed.risk_categories = [
                RiskCategory(cat) for cat in assumption_categories
            ]
    
    def _validate_output(self, decomposed: DecomposedIdea) -> None:
        """
        Validate LLM output meets all requirements
        
        Args:
            decomposed: Parsed DecomposedIdea object
            
        Raises:
            ValueError: If output doesn't meet constraints
        """
        num_assumptions = len(decomposed.assumptions)
        
        # Check assumption count
        if num_assumptions < MIN_ASSUMPTIONS:
            raise ValueError(
                f"Too few assumptions generated: {num_assumptions}. "
                f"Minimum {MIN_ASSUMPTIONS} required."
            )
        
        if num_assumptions > MAX_ASSUMPTIONS:
            raise ValueError(
                f"Too many assumptions generated: {num_assumptions}. "
                f"Maximum {MAX_ASSUMPTIONS} allowed."
            )
        
        # Validate assumption IDs (auto-fix if possible)
        self._validate_assumption_ids(decomposed)
        
        # Check for at least 2 critical assumptions (aligned with prompt requirement)
        critical_count = sum(
            1 for a in decomposed.assumptions 
            if self._normalize_value(a.importance) == "critical"
        )
        
        if critical_count < 2:
            raise ValueError(
                f"Need at least 2 critical assumptions. Found only {critical_count}. "
                f"The prompt requires 2-3 critical assumptions for proper risk analysis."
            )
        
        # Validate risk_categories alignment (auto-fix if possible)
        self._validate_risk_categories(decomposed)
    
    def decompose(self, idea: str, return_json: bool = True) -> Union[Dict, DecomposedIdea]:
        """
        Decompose a startup idea into structured assumptions
        
        Args:
            idea: User's startup idea in natural language
            return_json: If True (default), return dict; if False, return DecomposedIdea object
            
        Returns:
            dict (if return_json=True) or DecomposedIdea object (if return_json=False)
            
        Raises:
            ValueError: If input/output validation fails
            ValidationError: If LLM output doesn't match schema
        """
        # Validate input
        self._validate_input(idea)
        
        # Format prompt
        prompt = self.prompt_template.format(idea=idea.strip())
        
        # Call LLM with structured output (no need for json.loads!)
        try:
            # Directly get DecomposedIdea object from LLM
            decomposed = self.structured_llm.invoke(prompt)
            
            # Additional validation and auto-correction
            self._validate_output(decomposed)
            
            # Return based on return_json parameter
            if return_json:
                return decomposed.model_dump()
            else:
                return decomposed
            
        except ValidationError as e:
            raise ValueError(
                f"LLM output doesn't match expected schema: {str(e)}"
            )
        
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error during decomposition: {str(e)}"
            )
    
    def decompose_from_user_input(self, user_input: UserInput, return_json: bool = True) -> Union[Dict, DecomposedIdea]:
        """
        Convenience method to decompose from UserInput object
        
        Args:
            user_input: UserInput Pydantic object
            return_json: If True (default), return dict; if False, return DecomposedIdea object
            
        Returns:
            dict or DecomposedIdea object
        """
        return self.decompose(user_input.idea, return_json=return_json)


# ============================================================
# Convenience Functions
# ============================================================

def decompose_idea(
    idea: str,
    model_name: str = "gpt-4o",
    temperature: float = 0.3,
    return_json: bool = True
) -> Union[Dict, DecomposedIdea]:
    """
    Quick function to decompose an idea
    
    Args:
        idea: Startup idea text
        model_name: OpenAI model to use
        temperature: LLM temperature
        return_json: If True (default), return dict; if False, return DecomposedIdea object
        
    Returns:
        dict or DecomposedIdea object
    """
    decomposer = IdeaDecomposer(
        model_name=model_name,
        temperature=temperature
    )
    return decomposer.decompose(idea, return_json=return_json)


# ============================================================
# CLI Testing (Optional)
# ============================================================

if __name__ == "__main__":
    import sys
    
    # Simple CLI for testing
    if len(sys.argv) > 1:
        test_idea = " ".join(sys.argv[1:])
    else:
        test_idea = (
            "A social network for dog owners to arrange playdates "
            "in their neighborhood"
        )
    
    print("=" * 60)
    print("IDEA DECOMPOSER TEST")
    print("=" * 60)
    print(f"\nInput Idea:\n{test_idea}\n")
    print("Decomposing...\n")
    
    try:
        decomposer = IdeaDecomposer()
        
        # Get result as Pydantic object first (for structured access)
        result_obj = decomposer.decompose(test_idea, return_json=False)
        
        print("=" * 60)
        print("DECOMPOSITION RESULT")
        print("=" * 60)
        print(f"\nProduct Type: {result_obj.product_type}")
        print(f"Target User: {result_obj.target_user}")
        print(f"Value Prop: {result_obj.value_proposition}")
        print(f"\nAssumptions ({len(result_obj.assumptions)}):")
        
        for assumption in result_obj.assumptions:
            # Use _norm helper for safe printing
            category = assumption.category.value if hasattr(assumption.category, 'value') else assumption.category
            importance = assumption.importance.value if hasattr(assumption.importance, 'value') else assumption.importance
            
            print(f"\n  [{assumption.id}] ({category} - {importance})")
            print(f"  {assumption.assumption}")
        
        risk_cats = [cat.value if hasattr(cat, 'value') else cat for cat in result_obj.risk_categories]
        print(f"\nRisk Categories: {', '.join(risk_cats)}")
        print("\n" + "=" * 60)
        
        # Also print formatted JSON
        print("\nJSON Output:")
        result_json = result_obj.model_dump()
        print(json.dumps(result_json, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)