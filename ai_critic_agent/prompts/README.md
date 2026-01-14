# Prompt Engineering Module

This module contains the core prompts that define how the AI Critic Agent behaves and generates structured critiques of startup ideas.

## 📁 Files

### 1. `system.txt` - Agent Personality & Behavior
**Purpose**: Defines the AI Critic's core identity, behavioral principles, and output requirements.

**Key Characteristics**:
- Skeptical VC with 15+ years experience
- Evidence-driven, not emotional
- Professional but direct tone
- Default to skepticism

**Used by**: All LLM calls in the reasoning pipeline (system message)

---

### 2. `critique.txt` - Single Assumption Critique
**Purpose**: Instructs the LLM how to critique ONE assumption using evidence from the knowledge base.

**Input Schema**:
```python
{
  "assumption_id": str,
  "assumption_text": str,
  "category": str,
  "importance": str,
  "counter_evidence": {
    "assumption_type": str,
    "what_usually_happens": str,
    "why_it_fails": str,
    "sources": List[str]
  }
}
```

**Output Schema**:
```python
{
  "assumption_id": str,
  "assumption_text": str,
  "counterargument": str,        # 3-5 sentences
  "evidence_used": List[str],    # 2-4 specific facts
  "risk_level": str,             # "low" | "medium" | "high"
  "risk_justification": str      # 1-2 sentences
}
```

**Used by**: `reasoning/critic_agent.py` - called once per assumption

---

### 3. `summary.txt` - Final Report Generation
**Purpose**: Synthesizes all individual critiques into a cohesive final assessment.

**Input Schema**:
```python
{
  "decomposed_idea": DecomposedIdea,
  "critiques": List[SingleCritique]
}
```

**Output Schema**:
```python
{
  "idea_summary": str,           # 1-2 sentence objective summary
  "critiques": List[SingleCritique],  # Pass-through
  "overall_risk": str,           # "low" | "medium" | "high" | "critical"
  "key_concerns": List[str],     # 2-3 most fatal issues
  "final_assessment": str        # 2-3 paragraph synthesis
}
```

**Used by**: `reasoning/critic_agent.py` - called once at the end

---

## 🎯 Design Principles

### 1. Structured Output First
All prompts are designed to produce **parseable JSON** that other modules can consume programmatically.

### 2. Evidence-Based Reasoning
Every critique must be grounded in:
- Historical precedent
- Market patterns
- Business logic
- Data from the knowledge base

### 3. Calibrated Skepticism
- Use probability language ("usually", "typically", "rarely")
- Avoid absolutes unless strongly justified
- Distinguish between "hard" and "nearly impossible"

### 4. Professional Tone
- Direct but not cruel
- Analytical, not emotional
- Think "tough mentor" not "dismissive critic"

---

## 🔧 Integration Guide

### For Reasoning Agent Developers (人4)

```python
from pathlib import Path

# Load prompts
prompts_dir = Path("prompts")
system_prompt = (prompts_dir / "system.txt").read_text()
critique_prompt = (prompts_dir / "critique.txt").read_text()
summary_prompt = (prompts_dir / "summary.txt").read_text()

# Use in LLM calls
response = llm.invoke([
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": critique_prompt + "\n\n" + json.dumps(input_data)}
])
```

### Expected Flow

1. **System Prompt**: Loaded once at agent initialization
2. **Critique Loop**: For each assumption, call LLM with `critique.txt` + assumption data
3. **Summary**: Once all critiques are done, call LLM with `summary.txt` + all results

---

## 📊 Risk Level Calibration

### For `critique.txt` (Single Assumption)
- **HIGH**: Assumption nearly always wrong OR failure kills the business
- **MEDIUM**: Assumption often wrong OR failure severely damages business
- **LOW**: Assumption might be wrong BUT business can survive

**Important Note**: 
- Input `importance` field from decomposer uses: "critical", "important", "minor"
- Output `risk_level` field in critique uses: "high", "medium", "low"
- These are intentionally different - importance is about business impact if assumption is false, risk_level is about likelihood + impact combined

### For `summary.txt` (Overall Risk)
- **CRITICAL**: Multiple "high" risks, at least one existential
- **HIGH**: 1+ "high" risk, or many "medium" risks
- **MEDIUM**: Mostly "medium" risks, no "high" risks
- **LOW**: Predominantly "low" risks (rare)

---

## ✅ Validation Checklist

When modifying these prompts, ensure:

- [ ] Output is valid JSON
- [ ] All required fields are present
- [ ] Risk levels use only allowed values
- [ ] Tone remains skeptical but professional
- [ ] Evidence is referenced, not invented
- [ ] No motivational language or false hope

---

## 🧪 Testing Examples

### Quick Verification

Run the schema verification script to ensure all enum values are correct:

```bash
cd ai_critic_agent/prompts
python verify_schemas.py
```

This will check:
- ✅ JSON examples use correct enum values
- ✅ Prompt files reference correct categories and importance levels
- ✅ Documentation is consistent

### Example Files

See `examples/` folder for:
- Sample inputs for each prompt
- Expected outputs
- Edge cases (weak evidence, reasonable assumptions, etc.)

---

## 🤝 Cross-Module Dependencies

### Depends On:
- `common/schemas.py` - Data structures (DecomposedIdea, Assumption, etc.)
- `knowledge_base/retriever.py` - CounterEvidence format

### Used By:
- `reasoning/critic_agent.py` - Main reasoning loop
- `reasoning/formatter.py` - Output structuring

---

## 📝 Maintenance Notes

### When to Update These Prompts:

1. **Schema Changes**: If `common/schemas.py` changes, update input/output examples
2. **Tone Adjustments**: If user feedback suggests prompts are too harsh/soft
3. **Evidence Format**: If knowledge base changes how it returns data
4. **Risk Calibration**: If risk levels need recalibration based on real-world testing

### Change Log:
- 2024-XX-XX: Initial version created
- (Future updates here)

---

## 🎓 Prompt Engineering Best Practices Applied

1. **Clear Role Definition**: Agent knows exactly what it is (skeptical VC)
2. **Explicit Constraints**: Forbidden behaviors clearly stated
3. **Structured Examples**: JSON templates show exact output format
4. **Edge Case Handling**: Instructions for weak evidence, reasonable assumptions
5. **Calibrated Language**: Risk levels have precise definitions
6. **Modular Design**: Each prompt has a single, clear purpose

---

For questions or modifications, coordinate with:
- **人1** (Knowledge Base): Evidence format changes
- **人2** (Decomposer): Input schema changes
- **人4** (Reasoning): Integration and usage patterns
