"""
Critic Agent - Multi-stage LLM Reasoning with LangChain
Orchestrates decomposition → RAG retrieval → critique → verdict pipeline
"""

import os
import sys

# ===== MAC M4 PROTECTION =====
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

load_dotenv()

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from common.schemas import (
    DecomposedIdea,
    StartupAssumption,
    Critique,
    FinalVerdict,
    CriticResponse,
    EvaluationConfig,
    RiskLevel,
    SuccessProbability,
    RiskCategory,
)
from common.constants import get_overall_risk_from_critiques

from idea_decomposer.decomposer import IdeaDecomposer
from knowledge_base.retriever import CriticKnowledgeBase


class CriticAgent:
    """
    Multi-stage LLM reasoning agent for startup idea evaluation.

    Pipeline:
      1. Decompose idea into structured assumptions (IdeaDecomposer)
      2. Semantic evidence retrieval per assumption (FAISS RAG)
      3. Per-assumption critique via LangChain LCEL chain
      4. Final verdict synthesis via LangChain LCEL chain

    LangChain chains are built at initialization time and reused across calls,
    keeping per-request latency low.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        prompts_dir: str = "prompts",
        config: Optional[EvaluationConfig] = None,
    ):
        # EvaluationConfig drives model/temperature/thresholds when supplied
        self.config = config or EvaluationConfig()
        self.model_name = model_name or self.config.model_name or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.temperature = temperature or self.config.temperature

        self.prompts_dir = Path(prompts_dir)

        # Load prompt files
        self.system_prompt = self._load_prompt("system.txt")
        self.critique_prompt = self._load_prompt("critique.txt")
        self.summary_prompt = self._load_prompt("summary.txt")

        # LangChain LLM — JSON mode enforced via model_kwargs
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        # Shared JSON output parser
        self._json_parser = JsonOutputParser()

        # LCEL chains built once and reused
        self.critique_chain = self._build_critique_chain()
        self.verdict_chain = self._build_verdict_chain()

        # Sub-modules
        self.decomposer = IdeaDecomposer(model_name=self.model_name)
        self.knowledge_base = CriticKnowledgeBase()

    # ------------------------------------------------------------------
    # Chain construction (LangChain LCEL)
    # ------------------------------------------------------------------

    def _build_critique_chain(self):
        """
        Build the per-assumption critique chain.

        critique.txt already uses {assumption_id}, {assumption_text},
        {category}, {importance}, {evidence} as template variables.
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessagePromptTemplate.from_template(self.critique_prompt),
        ])
        return prompt | self.llm | self._json_parser

    def _build_verdict_chain(self):
        """
        Build the final verdict synthesis chain.

        summary.txt uses {input_data} as the single template variable.
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_prompt),
            HumanMessagePromptTemplate.from_template(self.summary_prompt),
        ])
        return prompt | self.llm | self._json_parser

    # ------------------------------------------------------------------
    # Prompt loading
    # ------------------------------------------------------------------

    def _load_prompt(self, filename: str) -> str:
        path = self.prompts_dir / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {path}")

    # ------------------------------------------------------------------
    # Evidence formatting
    # ------------------------------------------------------------------

    def _format_evidence_for_prompt(self, retrieval_result) -> List[Dict[str, Any]]:
        return [
            {
                "source": item.source,
                "content": item.content,
                "relevance_score": item.relevance_score,
                "category": item.category.value,
            }
            for item in retrieval_result.evidence
        ]

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def critique_idea(
        self,
        idea: str,
        config: Optional[EvaluationConfig] = None,
    ) -> CriticResponse:
        """
        Run the full multi-stage critique pipeline.

        Args:
            idea: Startup idea in natural language
            config: Optional per-request config override

        Returns:
            CriticResponse with all critiques and final verdict
        """
        cfg = config or self.config
        print(f"🔍 Analyzing idea: '{idea[:80]}...'")

        # Stage 1: Decompose
        print("\n📋 Stage 1: Decomposing idea into assumptions...")
        decomposed = self.decomposer.decompose(idea, return_json=False)

        # Apply max_assumptions cap from config
        if len(decomposed.assumptions) > cfg.max_assumptions:
            decomposed.assumptions = decomposed.assumptions[: cfg.max_assumptions]

        # Apply category filter if configured
        if cfg.focus_categories:
            decomposed.assumptions = [
                a for a in decomposed.assumptions
                if a.category in cfg.focus_categories
            ] or decomposed.assumptions  # fall back to all if filter too restrictive

        print(f"   ✅ {len(decomposed.assumptions)} assumptions identified")

        # Stage 2 + 3: Retrieve evidence & critique all assumptions in parallel
        n = len(decomposed.assumptions)
        print(f"\n💭 Stage 2–3: RAG retrieval + LangChain critique ({n} assumptions, parallel)...")

        from common.constants import RISK_LEVEL_SCORES

        def _critique_task(args: Tuple[int, StartupAssumption]):
            idx, assumption = args
            return idx, self._critique_assumption(assumption, decomposed, cfg)

        results: List[Optional[Critique]] = [None] * n

        with ThreadPoolExecutor(max_workers=min(n, 8)) as pool:
            futures = {
                pool.submit(_critique_task, (i, a)): i
                for i, a in enumerate(decomposed.assumptions)
            }
            for future in as_completed(futures):
                try:
                    idx, critique = future.result()
                    assumption_text = decomposed.assumptions[idx].assumption[:60]
                    if RISK_LEVEL_SCORES[critique.risk_level] >= RISK_LEVEL_SCORES[cfg.min_risk_threshold]:
                        results[idx] = critique
                        print(f"   ✅ [{idx+1}/{n}] {assumption_text}... → {critique.risk_level.value.upper()}")
                    else:
                        print(f"   ⏭️  [{idx+1}/{n}] {assumption_text}... → skipped (below threshold)")
                except Exception as e:
                    idx = futures[future]
                    print(f"   ⚠️  [{idx+1}/{n}] Error: {e}")

        critiques: List[Critique] = [r for r in results if r is not None]

        if not critiques:
            raise RuntimeError("No critiques generated — check assumptions and config thresholds")

        # Stage 4: Verdict synthesis
        print("\n⚖️  Stage 4: Synthesizing final verdict via LangChain chain...")
        verdict = self._generate_verdict(critiques, decomposed)
        print(f"   ✅ Overall risk: {verdict.overall_risk.value.upper()}")

        response = CriticResponse(
            idea_summary=decomposed.value_proposition,
            critiques=critiques,
            verdict=verdict,
        )
        print("\n✅ Critique complete!")
        return response

    # ------------------------------------------------------------------
    # Internal: per-assumption critique
    # ------------------------------------------------------------------

    def _critique_assumption(
        self,
        assumption: StartupAssumption,
        decomposed: DecomposedIdea,
        config: EvaluationConfig,
    ) -> Critique:
        """
        Critique one assumption using FAISS evidence + LangChain LCEL chain.
        """
        # RAG retrieval from FAISS knowledge base
        retrieval_result = self.knowledge_base.query(
            assumption=assumption.assumption,
            category=assumption.category,
            top_k=config.evidence_count,
        )
        evidence_list = self._format_evidence_for_prompt(retrieval_result)

        # Invoke the LangChain critique chain
        critique_dict = self.critique_chain.invoke({
            "assumption_id": assumption.id,
            "assumption_text": assumption.assumption,
            "category": assumption.category.value,
            "importance": assumption.importance.value,
            "evidence": json.dumps(evidence_list, indent=2, ensure_ascii=False),
        })

        return Critique(
            assumption_id=critique_dict["assumption_id"],
            assumption_text=critique_dict["assumption_text"],
            counterargument=critique_dict["counterargument"],
            evidence_used=critique_dict["evidence_used"],
            risk_level=RiskLevel(critique_dict["risk_level"]),
        )

    # ------------------------------------------------------------------
    # Internal: verdict synthesis
    # ------------------------------------------------------------------

    def _generate_verdict(
        self,
        critiques: List[Critique],
        decomposed: DecomposedIdea,
    ) -> FinalVerdict:
        """
        Synthesize a final verdict from all assumption critiques via LangChain chain.
        """
        critiques_serializable = [
            {
                "assumption_id": c.assumption_id,
                "assumption_text": c.assumption_text,
                "counterargument": c.counterargument,
                "evidence_used": c.evidence_used,
                "risk_level": c.risk_level.value,
            }
            for c in critiques
        ]

        analysis_input = json.dumps(
            {
                "decomposed_idea": decomposed.model_dump(),
                "critiques": critiques_serializable,
            },
            indent=2,
            ensure_ascii=False,
        )

        # Invoke the LangChain verdict chain
        summary_dict = self.verdict_chain.invoke({"input_data": analysis_input})

        # Overall risk: prefer LLM assessment, fall back to algorithmic calculation
        overall_risk = get_overall_risk_from_critiques(critiques)
        if "overall_risk" in summary_dict:
            try:
                overall_risk = RiskLevel(summary_dict["overall_risk"])
            except ValueError:
                pass

        success_probability = self._estimate_success_probability(overall_risk, critiques)

        return FinalVerdict(
            overall_risk=overall_risk,
            key_concerns=summary_dict.get("key_concerns", [])[:5],
            success_probability=success_probability,
            summary=summary_dict.get("final_assessment", ""),
        )

    def _estimate_success_probability(
        self,
        overall_risk: RiskLevel,
        critiques: List[Critique],
    ) -> SuccessProbability:
        critical_count = sum(1 for c in critiques if c.risk_level == RiskLevel.CRITICAL)
        high_count = sum(1 for c in critiques if c.risk_level == RiskLevel.HIGH)

        if overall_risk == RiskLevel.CRITICAL or critical_count >= 3:
            return SuccessProbability.VERY_LOW
        elif overall_risk == RiskLevel.HIGH or (critical_count >= 1 and high_count >= 2):
            return SuccessProbability.LOW
        else:
            return SuccessProbability.MODERATE


# ============================================================
# Convenience function
# ============================================================

def critique_startup_idea(
    idea: str,
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
    config: Optional[EvaluationConfig] = None,
) -> CriticResponse:
    """Run a one-shot critique with optional EvaluationConfig."""
    agent = CriticAgent(model_name=model_name, temperature=temperature, config=config)
    return agent.critique_idea(idea)


# ============================================================
# CLI Testing
# ============================================================

if __name__ == "__main__":
    from reasoning.formatter import CriticFormatter

    test_idea = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "A social network for dog owners to arrange playdates in their neighborhood"
    )

    print("=" * 80)
    print("CRITIC AGENT TEST")
    print("=" * 80)
    print(f"\nIdea: {test_idea}\n")

    try:
        agent = CriticAgent()
        response = agent.critique_idea(test_idea)

        formatter = CriticFormatter()
        print("\n" + "=" * 80)
        print(formatter.to_text(response, verbose=True))

        with open("critique_output.json", "w", encoding="utf-8") as f:
            f.write(response.model_dump_json(indent=2))
        print("\n✅ JSON saved to critique_output.json")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
