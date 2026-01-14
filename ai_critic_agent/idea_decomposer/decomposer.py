"""
Idea Decomposer - OpenAI Ultimate Anti-Cache Version
Forces fresh analysis for each idea
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

from openai import OpenAI
from pydantic import ValidationError

from common.schemas import DecomposedIdea, ImportanceLevel
from common.constants import MIN_IDEA_LENGTH, MAX_IDEA_LENGTH, MIN_ASSUMPTIONS, MAX_ASSUMPTIONS


class IdeaDecomposer:
    """Decomposes startup ideas with anti-cache mechanisms"""
    
    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.9):
        if model_name is None:
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        self.model_name = model_name
        self.temperature = temperature
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def _validate_input(self, idea: str) -> None:
        if not idea or not idea.strip():
            raise ValueError("Idea cannot be empty")
        if len(idea) < MIN_IDEA_LENGTH:
            raise ValueError(f"Idea too short. Minimum {MIN_IDEA_LENGTH} characters.")
        if len(idea) > MAX_IDEA_LENGTH:
            raise ValueError(f"Idea too long. Maximum {MAX_IDEA_LENGTH} characters.")
    
    def _build_focused_prompt(self, idea: str) -> tuple:
        """Build highly focused prompt with uniqueness markers"""
        
        # Generate unique markers
        idea_hash = hashlib.md5(idea.encode()).hexdigest()[:12]
        session_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time() * 1000)
        
        # Extract distinctive keywords
        words = idea.lower().split()
        key_nouns = [w for w in words if len(w) > 3][:5]
        
        system_prompt = f"""You are a startup idea analyzer. Session: {session_id}.

CRITICAL: You must analyze a NEW idea in THIS request. 
Do NOT reuse any previous analysis.
Do NOT analyze graphic designers, e-commerce, or AI tutors.

Return ONLY valid JSON with these exact keys:
- original_idea (string)
- product_type (string)
- target_user (string)
- value_proposition (string)
- assumptions (array of 5-8 objects)
- risk_categories (array of strings)

Each assumption object needs:
- id (string: "assumption_1", "assumption_2", etc.)
- assumption (string)
- category (string: market/competition/execution/monetization/user_behavior/timing)
- importance (string: critical/important/minor)

Use "assumptions" NOT "critical_assumptions" as the key."""

        user_prompt = f"""[NEW ANALYSIS REQUEST - ID: {idea_hash} - Time: {timestamp}]

ANALYZE THIS SPECIFIC IDEA (not any previous one):

\"\"\"{idea}\"\"\"

Key concepts in THIS idea: {', '.join(key_nouns)}

Requirements:
1. Set "original_idea" to exactly: "{idea}"
2. Identify what THIS idea is about (keywords: {key_nouns[:3]})
3. Generate 5-8 assumptions specific to THIS idea
4. Use "assumptions" as the JSON key (not "critical_assumptions")
5. At least 2 assumptions must be "critical" importance

Return ONLY the JSON object, starting with {{"""

        return system_prompt, user_prompt
    
    def decompose(self, idea: str, return_json: bool = True) -> Union[Dict, DecomposedIdea]:
        """Decompose startup idea with anti-cache protection"""
        
        self._validate_input(idea)
        
        # Build focused prompt
        system_prompt, user_prompt = self._build_focused_prompt(idea)
        
        try:
            # Call with maximum uniqueness
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,  # Higher temp for variety
                response_format={"type": "json_object"},
                seed=None,
                user=f"decomposer_{uuid.uuid4().hex[:16]}"
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON
            cleaned = response_text.strip()
            if "```" in cleaned:
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end+1]
            
            data = json.loads(cleaned)
            
            # Critical fixes
            # 1. Fix key name
            if "critical_assumptions" in data:
                data["assumptions"] = data.pop("critical_assumptions")
            
            # 2. FORCE original_idea
            data["original_idea"] = idea
            
            # 3. Check if response is about the right topic
            response_lower = json.dumps(data).lower()
            idea_keywords = set(idea.lower().split()[:5])
            
            found_keywords = sum(1 for keyword in idea_keywords if keyword in response_lower)
            
            if found_keywords < 2:
                print(f"\n⚠️  WARNING: LLM may have analyzed wrong idea!")
                print(f"   Expected keywords: {idea_keywords}")
                print(f"   Found: {found_keywords}")
                print(f"   Forcing original_idea to match input...")
            
            # 4. Fix IDs
            for i, a in enumerate(data.get("assumptions", []), 1):
                a["id"] = f"assumption_{i}"
            
            # 5. Sync categories
            if data.get("assumptions"):
                categories = list(set(a["category"] for a in data["assumptions"]))
                data["risk_categories"] = categories
            
            # 6. Validate count
            num = len(data.get("assumptions", []))
            if num < MIN_ASSUMPTIONS:
                raise ValueError(f"Too few assumptions: {num}")
            if num > MAX_ASSUMPTIONS:
                data["assumptions"] = data["assumptions"][:MAX_ASSUMPTIONS]
            
            # 7. Ensure 2+ critical
            critical = sum(1 for a in data["assumptions"] if a.get("importance") == "critical")
            if critical < 2:
                for i in range(min(2, len(data["assumptions"]))):
                    data["assumptions"][i]["importance"] = "critical"
            
            # Build Pydantic
            decomposed = DecomposedIdea(**data)
            
            if return_json:
                return decomposed.model_dump()
            else:
                return decomposed
                
        except Exception as e:
            raise RuntimeError(f"Decomposition failed: {e}")


if __name__ == "__main__":
    import sys
    
    test_idea = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Pet uber platform"
    
    print(f"Input: '{test_idea}'\n")
    
    decomposer = IdeaDecomposer()
    result = decomposer.decompose(test_idea, return_json=False)
    
    print(f"Original: {result.original_idea}")
    print(f"Product: {result.product_type}")
    print(f"Value: {result.value_proposition}")
    print(f"\nAssumptions:")
    for a in result.assumptions[:3]:
        print(f"  - {a.assumption}")
    
    # Verify
    input_words = set(test_idea.lower().split())
    output_words = set(result.value_proposition.lower().split())
    overlap = input_words & output_words
    
    if len(overlap) >= 1:
        print(f"\n✅ Match found: {overlap}")
    else:
        print(f"\n⚠️  No clear match")