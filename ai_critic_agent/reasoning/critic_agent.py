"""
Critic Agent - Main Reasoning & Orchestration
Coordinates all modules to generate structured critiques
Uses Anthropic Claude for reliable LLM calls
"""

import os
import sys

# ===== MAC M4 PROTECTION =====
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

from common.schemas import (
    DecomposedIdea,
    StartupAssumption,
    Critique,
    FinalVerdict,
    CriticResponse,
    RiskLevel,
    SuccessProbability,
    RiskCategory
)
from common.constants import get_overall_risk_from_critiques

from idea_decomposer.decomposer import IdeaDecomposer
from knowledge_base.retriever import CriticKnowledgeBase


class CriticAgent:
    """
    Main Critic Agent
    
    Orchestrates the complete critique pipeline:
    1. Decompose idea into assumptions (via IdeaDecomposer)
    2. Query knowledge base for each assumption
    3. Generate critiques using LLM + evidence + prompts
    4. Synthesize final verdict
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        prompts_dir: str = "prompts"
    ):
        """Initialize the Critic Agent"""
        
        # Read model from env
        if model_name is None:
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.prompts_dir = Path(prompts_dir)
        
        # Initialize sub-modules
        self.decomposer = IdeaDecomposer()
        self.knowledge_base = CriticKnowledgeBase()
        
        # Load prompts
        self.system_prompt = self._load_prompt("system.txt")
        self.critique_prompt = self._load_prompt("critique.txt")
        self.summary_prompt = self._load_prompt("summary.txt")
    
    def _load_prompt(self, filename: str) -> str:
        """Load a prompt file as plain text"""
        path = self.prompts_dir / filename
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {path}")
    
    def _clean_json_response(self, response: str) -> str:
        """
        Clean LLM response to extract valid JSON
        
        LLM might wrap JSON in markdown code blocks or add explanations
        """
        response = response.strip()
        
        # Remove markdown code blocks
        if "```json" in response:
            # Extract content between ```json and ```
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end != -1:
                response = response[start:end]
        elif "```" in response:
            # Extract content between ``` and ```
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                response = response[start:end]
        
        response = response.strip()
        
        # Find JSON object boundaries
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1:
            response = response[start:end+1]
        
        return response
    
    def _parse_json_safely(self, response_text: str, context: str = "") -> dict:
        """
        Safely parse JSON with better error reporting
        
        Args:
            response_text: Raw LLM response
            context: Description of what's being parsed (for error messages)
            
        Returns:
            dict: Parsed JSON
            
        Raises:
            ValueError: If JSON cannot be parsed
        """
        try:
            cleaned = self._clean_json_response(response_text)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Print debug info
            print(f"\n⚠️  JSON Parse Error in {context}:")
            print(f"   Error: {e}")
            print(f"   Position: line {e.lineno}, column {e.colno}")
            print(f"\n   Raw response (first 500 chars):")
            print(f"   {response_text[:500]}")
            print(f"\n   Cleaned response (first 500 chars):")
            cleaned = self._clean_json_response(response_text)
            print(f"   {cleaned[:500]}")
            
            raise ValueError(
                f"Failed to parse {context} as JSON. "
                f"LLM may have returned malformed JSON or included extra text."
            )
    
    def _format_evidence_for_prompt(
        self,
        retrieval_result
    ) -> List[Dict[str, Any]]:
        """
        Format RetrievalResult into structure expected by critique prompt
        
        Args:
            retrieval_result: RetrievalResult from knowledge base
            
        Returns:
            List of evidence dicts for prompt
        """
        evidence_list = []
        
        for item in retrieval_result.evidence:
            evidence_list.append({
                "source": item.source,
                "content": item.content,
                "relevance_score": item.relevance_score,
                "category": item.category.value  # Enum → str
            })
        
        return evidence_list
    
    def critique_idea(self, idea: str) -> CriticResponse:
        """
        Main method: Complete critique pipeline
        
        Args:
            idea: User's startup idea (natural language)
            
        Returns:
            CriticResponse: Complete structured critique
        """
        print(f"🔍 Analyzing idea: '{idea[:80]}...'")
        
        # Step 1: Decompose idea
        print("\n📋 Step 1: Decomposing idea...")
        decomposed = self.decomposer.decompose(idea, return_json=False)
        print(f"   ✅ Found {len(decomposed.assumptions)} assumptions")
        
        # Step 2: Critique each assumption
        print("\n💭 Step 2: Generating critiques...")
        critiques = []
        
        for i, assumption in enumerate(decomposed.assumptions, 1):
            print(f"   [{i}/{len(decomposed.assumptions)}] {assumption.assumption[:60]}...")
            
            try:
                critique = self._critique_assumption(assumption, decomposed)
                critiques.append(critique)
                print(f"      → Risk: {critique.risk_level.value.upper()}")
            except Exception as e:
                print(f"      ⚠️  Error: {e}")
                # Continue with other assumptions
                continue
        
        if not critiques:
            raise RuntimeError("Failed to generate any critiques")
        
        # Step 3: Generate final verdict
        print("\n⚖️  Step 3: Synthesizing verdict...")
        verdict = self._generate_verdict(critiques, decomposed)
        print(f"   ✅ Overall risk: {verdict.overall_risk.value.upper()}")
        
        # Step 4: Build response
        response = CriticResponse(
            idea_summary=decomposed.value_proposition,
            critiques=critiques,
            verdict=verdict
        )
        
        print("\n✅ Critique complete!")
        return response
    
    def _critique_assumption(
        self,
        assumption: StartupAssumption,
        decomposed: DecomposedIdea
    ) -> Critique:
        """
        Critique a single assumption
        
        Args:
            assumption: The assumption to critique
            decomposed: Full decomposed idea for context
            
        Returns:
            Critique: Structured critique with counterarguments
        """
        # Query knowledge base for evidence
        retrieval_result = self.knowledge_base.query(
            assumption=assumption.assumption,
            category=assumption.category,
            top_k=5
        )
        
        # Format evidence for prompt
        evidence_list = self._format_evidence_for_prompt(retrieval_result)
        
        # Format evidence as JSON
        evidence_json = json.dumps(evidence_list, indent=2, ensure_ascii=False)
        
        # Build critique prompt
        critique_user_prompt = f"""Analyze this assumption:

Assumption ID: {assumption.id}
Assumption: {assumption.assumption}
Category: {assumption.category.value}
Importance: {assumption.importance.value}

Evidence from knowledge base:
{evidence_json}

Following the instructions in your system prompt, generate a critique as a JSON object."""
        
        # Call OpenAI
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt + "\n\n" + self.critique_prompt},
                    {"role": "user", "content": critique_user_prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            
        except Exception as e:
            raise ValueError(f"OpenAI API call failed: {e}")
        
        # Parse JSON response with better error handling
        try:
            critique_dict = self._parse_json_safely(
                response_text, 
                context=f"critique for {assumption.id}"
            )
        except ValueError as e:
            # Log error and skip this assumption
            print(f"      ⚠️  JSON parse failed, skipping: {e}")
            raise
        
        # Validate required fields
        required_fields = ["assumption_id", "assumption_text", "counterargument", 
                          "evidence_used", "risk_level"]
        missing_fields = [f for f in required_fields if f not in critique_dict]
        
        if missing_fields:
            raise ValueError(
                f"LLM response missing required fields: {missing_fields}\n"
                f"Response: {response_text[:200]}..."
            )
        
        # Build Critique object
        critique = Critique(
            assumption_id=critique_dict["assumption_id"],
            assumption_text=critique_dict["assumption_text"],
            counterargument=critique_dict["counterargument"],
            evidence_used=critique_dict["evidence_used"],
            risk_level=RiskLevel(critique_dict["risk_level"])  # str → Enum
        )
        
        return critique
    
    def _generate_verdict(
        self,
        critiques: List[Critique],
        decomposed: DecomposedIdea
    ) -> FinalVerdict:
        """
        Generate final overall verdict
        
        Args:
            critiques: List of all assumption critiques
            decomposed: Decomposed idea for context
            
        Returns:
            FinalVerdict: Overall assessment
        """
        # Prepare input for summary prompt
        decomposed_dict = decomposed.model_dump()
        
        # Convert critiques to dicts with Enum → str
        critiques_dict = []
        for c in critiques:
            critiques_dict.append({
                "assumption_id": c.assumption_id,
                "assumption_text": c.assumption_text,
                "counterargument": c.counterargument,
                "evidence_used": c.evidence_used,
                "risk_level": c.risk_level.value  # Enum → str
            })
        
        # Format input as JSON
        summary_input = {
            "decomposed_idea": decomposed_dict,
            "critiques": critiques_dict
        }
        
        summary_json = json.dumps(summary_input, indent=2, ensure_ascii=False)
        
        # Build summary prompt
        summary_user_prompt = f"""Synthesize the final verdict for this startup analysis:

{summary_json}

Following the instructions in your system prompt, generate the final assessment as a JSON object."""
        
        # Call OpenAI
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt + "\n\n" + self.summary_prompt},
                    {"role": "user", "content": summary_user_prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            
        except Exception as e:
            raise ValueError(f"OpenAI API call failed: {e}")
        
        # Parse JSON response with better error handling
        try:
            summary_dict = self._parse_json_safely(
                response_text,
                context="summary verdict"
            )
        except ValueError as e:
            print(f"\n⚠️  Summary JSON parse failed: {e}")
            raise
        
        # Calculate overall risk (use helper from constants)
        overall_risk = get_overall_risk_from_critiques(critiques)
        
        # Override if LLM provided a different assessment
        if "overall_risk" in summary_dict:
            try:
                overall_risk = RiskLevel(summary_dict["overall_risk"])
            except ValueError:
                pass  # Keep calculated value
        
        # Map risk to success probability
        success_probability = self._estimate_success_probability(overall_risk, critiques)
        
        # Build FinalVerdict
        verdict = FinalVerdict(
            overall_risk=overall_risk,
            key_concerns=summary_dict.get("key_concerns", [])[:5],  # Max 5
            success_probability=success_probability,
            summary=summary_dict.get("final_assessment", "")
        )
        
        return verdict
    
    def _estimate_success_probability(
        self,
        overall_risk: RiskLevel,
        critiques: List[Critique]
    ) -> SuccessProbability:
        """
        Map overall risk to success probability
        
        Args:
            overall_risk: Overall risk level
            critiques: All critiques
            
        Returns:
            SuccessProbability enum value
        """
        critical_count = sum(1 for c in critiques if c.risk_level == RiskLevel.CRITICAL)
        high_count = sum(1 for c in critiques if c.risk_level == RiskLevel.HIGH)
        
        # Decision matrix
        if overall_risk == RiskLevel.CRITICAL or critical_count >= 3:
            return SuccessProbability.VERY_LOW
        elif overall_risk == RiskLevel.HIGH or (critical_count >= 1 and high_count >= 2):
            return SuccessProbability.LOW
        else:
            return SuccessProbability.MODERATE


# ============================================================
# Convenience Function
# ============================================================

def critique_startup_idea(
    idea: str,
    model_name: str = "gpt-4o",
    temperature: float = 0.7
) -> CriticResponse:
    """
    Quick function to critique a startup idea
    
    Args:
        idea: Startup idea text
        model_name: OpenAI model to use
        temperature: LLM temperature
        
    Returns:
        CriticResponse: Complete critique
    """
    agent = CriticAgent(
        model_name=model_name,
        temperature=temperature
    )
    return agent.critique_idea(idea)


# ============================================================
# CLI Testing
# ============================================================

if __name__ == "__main__":
    import sys
    from reasoning.formatter import CriticFormatter
    
    # Test idea
    if len(sys.argv) > 1:
        test_idea = " ".join(sys.argv[1:])
    else:
        test_idea = "A social network for dog owners to arrange playdates in their neighborhood"
    
    print("=" * 80)
    print("CRITIC AGENT TEST")
    print("=" * 80)
    print(f"\nIdea: {test_idea}\n")
    
    try:
        # Run critique
        agent = CriticAgent()
        response = agent.critique_idea(test_idea)
        
        # Format output
        formatter = CriticFormatter()
        
        print("\n" + "=" * 80)
        print("FORMATTED OUTPUT")
        print("=" * 80)
        print(formatter.to_text(response, verbose=True))
        
        # Save JSON
        with open("critique_output.json", "w", encoding="utf-8") as f:
            f.write(response.model_dump_json(indent=2))
        print("\n✅ JSON saved to critique_output.json")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)