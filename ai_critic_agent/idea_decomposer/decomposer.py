"""
Idea Decomposer — LangChain-powered startup idea parser
Breaks a raw idea into structured assumptions with anti-cache mechanisms
"""
import os
import json
import hashlib
import uuid
import time
from pathlib import Path
from typing import Optional, Union, Dict

from dotenv import load_dotenv

load_dotenv()

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError

from common.schemas import DecomposedIdea, ImportanceLevel
from common.constants import MIN_IDEA_LENGTH, MAX_IDEA_LENGTH, MIN_ASSUMPTIONS, MAX_ASSUMPTIONS


class IdeaDecomposer:
    """
    Decomposes startup ideas into structured assumptions using a LangChain chain.

    Anti-cache mechanisms (session ID, timestamp, idea hash) are injected into
    the prompt at call time to prevent the LLM from returning stale or cached
    analyses across requests.
    """

    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.9):
        if model_name is None:
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o")

        self.model_name = model_name
        self.temperature = temperature

        # LangChain LLM with JSON mode
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        self._json_parser = JsonOutputParser()

    def _validate_input(self, idea: str) -> None:
        if not idea or not idea.strip():
            raise ValueError("Idea cannot be empty")
        if len(idea) < MIN_IDEA_LENGTH:
            raise ValueError(f"Idea too short. Minimum {MIN_IDEA_LENGTH} characters.")
        if len(idea) > MAX_IDEA_LENGTH:
            raise ValueError(f"Idea too long. Maximum {MAX_IDEA_LENGTH} characters.")

    def _build_chain(self, session_id: str):
        """
        Build a LangChain chain with session-specific system prompt to defeat caching.
        """
        system_content = (
            f"You are a startup idea analyzer. Session: {session_id}.\n\n"
            "CRITICAL: You must analyze a NEW idea in THIS request. "
            "Do NOT reuse any previous analysis.\n"
            "Do NOT analyze graphic designers, e-commerce, or AI tutors.\n\n"
            "Return ONLY valid JSON with these exact keys:\n"
            "- original_idea (string)\n"
            "- product_type (string)\n"
            "- target_user (string)\n"
            "- value_proposition (string)\n"
            "- assumptions (array of 5-8 objects)\n"
            "- risk_categories (array of strings)\n\n"
            "Each assumption object needs:\n"
            "- id (string: \"assumption_1\", \"assumption_2\", etc.)\n"
            "- assumption (string)\n"
            "- category (string: market/competition/execution/monetization/user_behavior/timing)\n"
            "- importance (string: critical/important/minor)\n\n"
            "Use \"assumptions\" NOT \"critical_assumptions\" as the key."
        )

        human_template = (
            "[NEW ANALYSIS REQUEST - ID: {idea_hash} - Time: {timestamp}]\n\n"
            "ANALYZE THIS SPECIFIC IDEA (not any previous one):\n\n"
            "\"\"\"{idea}\"\"\"\n\n"
            "Key concepts in THIS idea: {key_nouns}\n\n"
            "Requirements:\n"
            "1. Set \"original_idea\" to exactly: \"{idea}\"\n"
            "2. Identify what THIS idea is about (keywords: {key_nouns})\n"
            "3. Generate 5-8 assumptions specific to THIS idea\n"
            "4. Use \"assumptions\" as the JSON key (not \"critical_assumptions\")\n"
            "5. At least 2 assumptions must be \"critical\" importance\n\n"
            "Return ONLY the JSON object, starting with {{"
        )

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_content),
            HumanMessagePromptTemplate.from_template(human_template),
        ])
        return prompt | self.llm | self._json_parser

    def decompose(self, idea: str, return_json: bool = True) -> Union[Dict, DecomposedIdea]:
        """
        Decompose a startup idea into structured assumptions.

        Args:
            idea: Raw startup idea text
            return_json: If True, return dict; if False, return DecomposedIdea

        Returns:
            dict or DecomposedIdea
        """
        self._validate_input(idea)

        # Build uniqueness markers for anti-cache
        idea_hash = hashlib.md5(idea.encode()).hexdigest()[:12]
        session_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time() * 1000)
        words = idea.lower().split()
        key_nouns = ", ".join(w for w in words if len(w) > 3)[:5] or idea[:30]

        chain = self._build_chain(session_id)

        try:
            data = chain.invoke({
                "idea_hash": idea_hash,
                "timestamp": timestamp,
                "idea": idea,
                "key_nouns": key_nouns,
            })

            # ---- Post-processing & validation ----

            # Fix alternate key name returned by some model versions
            if "critical_assumptions" in data:
                data["assumptions"] = data.pop("critical_assumptions")

            # Always enforce the original idea text
            data["original_idea"] = idea

            # Warn if response doesn't seem related to the input
            response_lower = json.dumps(data).lower()
            idea_keywords = set(idea.lower().split()[:5])
            found_keywords = sum(1 for kw in idea_keywords if kw in response_lower)
            if found_keywords < 2:
                print(f"\n⚠️  WARNING: LLM may have analyzed wrong idea!")
                print(f"   Expected keywords: {idea_keywords}")
                print(f"   Found: {found_keywords}")

            # Normalize assumption IDs and sanitize categories
            valid_categories = {"market", "execution", "competition", "monetization", "user_behavior", "timing", "general"}
            for i, a in enumerate(data.get("assumptions", []), 1):
                a["id"] = f"assumption_{i}"
                if a.get("category") not in valid_categories:
                    a["category"] = "general"

            # Keep risk_categories in sync with actual assumptions
            if data.get("assumptions"):
                data["risk_categories"] = list(
                    {a["category"] for a in data["assumptions"]}
                )

            # Enforce count bounds
            num = len(data.get("assumptions", []))
            if num < MIN_ASSUMPTIONS:
                raise ValueError(f"Too few assumptions: {num}")
            if num > MAX_ASSUMPTIONS:
                data["assumptions"] = data["assumptions"][:MAX_ASSUMPTIONS]

            # Ensure at least 2 critical assumptions
            critical = sum(
                1 for a in data["assumptions"] if a.get("importance") == "critical"
            )
            if critical < 2:
                for i in range(min(2, len(data["assumptions"]))):
                    data["assumptions"][i]["importance"] = "critical"

            decomposed = DecomposedIdea(**data)
            return decomposed.model_dump() if return_json else decomposed

        except Exception as e:
            raise RuntimeError(f"Decomposition failed: {e}")


if __name__ == "__main__":
    import sys

    test_idea = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Pet uber platform"
    print(f"Input: '{test_idea}'\n")

    decomposer = IdeaDecomposer()
    result = decomposer.decompose(test_idea, return_json=False)

    print(f"Original: {result.original_idea}")
    print(f"Product:  {result.product_type}")
    print(f"Value:    {result.value_proposition}")
    print(f"\nAssumptions:")
    for a in result.assumptions[:3]:
        print(f"  - [{a.category.value}] {a.assumption}")

    input_words = set(test_idea.lower().split())
    output_words = set(result.value_proposition.lower().split())
    overlap = input_words & output_words
    print(f"\n{'✅' if overlap else '⚠️ '} Keyword overlap: {overlap or 'none'}")
