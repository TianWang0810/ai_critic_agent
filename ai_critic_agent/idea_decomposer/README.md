# Idea Decomposer Module

**Owner**: ai_critic_agent
**Status**: ✅ Complete  
**Last Updated**: 2024-12-13

## Purpose

The Idea Decomposer takes a raw startup idea (natural language input) and breaks it down into:
- Product type classification
- Target user segment
- Core value proposition
- Structured, testable assumptions with risk categorization
- Risk categories summary

This provides the foundation for the AI Critic Agent to systematically challenge each assumption using the knowledge base.

---

## Module Interface

### Input
```python
from common.schemas import UserInput

user_input = UserInput(
    idea="A social network for dog owners to arrange playdates"
)
```

### Output (JSON by default)
```python
{
  "original_idea": "A social network for dog owners...",
  "product_type": "Consumer mobile app / Social network",
  "target_user": "Dog owners in urban/suburban areas...",
  "value_proposition": "Connect nearby dog owners to easily schedule...",
  "assumptions": [
    {
      "id": "assumption_1",
      "category": "market",
      "assumption": "Dog owners actively seek playdates...",
      "importance": "critical"
    },
    ...
  ],
  "risk_categories": ["market", "user_behavior", "competition", "execution", "monetization"]
}
```

---

## Architecture Highlights

### ✨ Key Features

1. **Pydantic Structured Output** (NOT `json.loads`)
   - Uses `llm.with_structured_output(DecomposedIdea)` 
   - Directly returns validated Pydantic objects
   - Much more stable than manual JSON parsing

2. **Automatic Validation & Correction**
   - Enforces `assumption_1`, `assumption_2`, ... format
   - Detects and fixes duplicate IDs
   - Auto-aligns `risk_categories` with assumption categories
   - Requires at least 2 critical assumptions (per prompt spec)

3. **Flexible Output Format**
   - Returns JSON dict by default (for module integration)
   - Can return Pydantic object for type safety
   - Seamless conversion between formats

---

## Usage

### Basic Usage

```python
from idea_decomposer.decomposer import IdeaDecomposer

# Initialize
decomposer = IdeaDecomposer()

# Decompose an idea (returns JSON dict by default)
idea = "An AI tutor app for college students"
result = decomposer.decompose(idea)

# Access as dictionary
print(f"Product Type: {result['product_type']}")
print(f"Target User: {result['target_user']}")
print(f"Number of Assumptions: {len(result['assumptions'])}")

# Iterate through assumptions
for assumption in result['assumptions']:
    print(f"  [{assumption['id']}] {assumption['assumption']}")
    print(f"  Category: {assumption['category']} | Importance: {assumption['importance']}")
```

### Get Pydantic Object (for type checking)

```python
# Return Pydantic object instead of dict
result = decomposer.decompose(idea, return_json=False)

# Type-safe access
print(result.target_user)  # IDE autocomplete works
print(result.assumptions[0].category)  # Enum type

# Convert to JSON when needed
json_result = result.model_dump()
```

### Quick Function

```python
from idea_decomposer.decomposer import decompose_idea

# One-liner for quick decomposition
result = decompose_idea("Your startup idea here")
# Returns JSON dict by default
```

### Integration with Other Modules

```python
# Use in pipeline
from idea_decomposer.decomposer import IdeaDecomposer
from knowledge_base.retriever import CriticRetriever

decomposer = IdeaDecomposer()
retriever = CriticRetriever("knowledge_base/index")

# Step 1: Decompose idea
decomposed = decomposer.decompose(user_idea, return_json=True)

# Step 2: For each assumption, retrieve counter-evidence
for assumption in decomposed['assumptions']:
    evidence = retriever.retrieve(assumption['assumption'], k=4)
    # Pass to reasoning agent...
```

---

## Configuration

### Environment Variables

**Required**: Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file:
```
OPENAI_API_KEY=sk-...
```

### Initialization Parameters

```python
decomposer = IdeaDecomposer(
    model_name="gpt-4o",           # OpenAI model to use
    temperature=0.3,                # Lower = more consistent (0.0-1.0)
    prompt_path="custom_prompt.txt" # Optional: custom prompt template
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_name` | `"gpt-4o"` | OpenAI model identifier |
| `temperature` | `0.3` | Creativity level (0.0 = deterministic, 1.0 = creative) |
| `prompt_path` | `prompts/idea_decompose.txt` | Path to prompt template file |

### Constraints (from `constants.py`)

| Constraint | Value | Purpose |
|------------|-------|---------|
| `MIN_IDEA_LENGTH` | 10 chars | Prevent empty inputs |
| `MAX_IDEA_LENGTH` | 1000 chars | Prevent excessive inputs |
| `MIN_ASSUMPTIONS` | 3 | Ensure sufficient analysis depth |
| `MAX_ASSUMPTIONS` | 15 | Prevent over-generation |
| **Minimum Critical** | 2 | Aligned with prompt requirement (2-3 critical) |

---

## File Structure

```
idea_decomposer/
├── README.md              # This file - comprehensive documentation
├── decomposer.py          # Main implementation with Pydantic structured output
├── test_decomposer.py     # Unit tests
└── prompts/
    └── idea_decompose.txt # LLM prompt template (IMPORTANT: read below)
```

---

## Prompt Template Location

⚠️ **Important for team collaboration**

The prompt template is located at:
```
idea_decomposer/prompts/idea_decompose.txt
```

### Customizing the Prompt

**Option 1: Edit the default file directly**
```bash
# Edit this file
vim idea_decomposer/prompts/idea_decompose.txt
```

**Option 2: Use a custom prompt file**
```python
decomposer = IdeaDecomposer(
    prompt_path="path/to/your/custom_prompt.txt"
)
```

### Prompt Requirements

Your prompt file **must**:
- Contain the `{idea}` placeholder for user input
- Instruct the model to generate 5-8 assumptions
- Require at least 2-3 assumptions marked as "critical"
- Cover at least 3 different risk categories
- Output must match `DecomposedIdea` schema structure

Example placeholder usage:
```
Analyze the following startup idea: {idea}
```

---

## How It Works

### 1. Structured Output Pipeline

```
User Idea (string)
    ↓
Prompt Template (idea_decompose.txt)
    ↓
LLM with Pydantic Schema (gpt-4o)
    ↓
DecomposedIdea Object (validated)
    ↓
Auto-validation & Correction
    ↓
JSON dict (or Pydantic object)
```

### 2. Validation Layers

**Layer 1: Input Validation**
- Length checks (10-1000 characters)
- Non-empty validation

**Layer 2: Pydantic Schema Validation**
- Type checking (automatic with structured output)
- Enum validation for categories
- Field presence validation

**Layer 3: Business Logic Validation**
- Assumption count (3-15)
- Minimum 2 critical assumptions
- Assumption ID format enforcement (`assumption_1`, `assumption_2`, ...)
- ID uniqueness check
- Risk categories alignment with assumptions

**Layer 4: Auto-correction**
- Fixes malformed assumption IDs
- Regenerates risk_categories if mismatched
- Maintains data consistency

### 3. Why Pydantic Structured Output?

**Old approach (unstable):**
```python
response = llm.invoke(prompt)
text = response.content
parsed = json.loads(text)  # ❌ Can fail, needs error handling
decomposed = DecomposedIdea(**parsed)
```

**New approach (stable):**
```python
structured_llm = llm.with_structured_output(DecomposedIdea)
decomposed = structured_llm.invoke(prompt)  # ✅ Guaranteed valid object
```

Benefits:
- No `json.loads()` failure points
- Automatic schema validation
- Type safety guaranteed
- LangChain + OpenAI handles formatting

---

## Example Output

### Input
```
"A social network for dog owners to arrange playdates in their neighborhood"
```

### Output (JSON)
```json
{
  "original_idea": "A social network for dog owners to arrange playdates in their neighborhood",
  "product_type": "Consumer mobile app / Social network",
  "target_user": "Dog owners in urban/suburban areas who actively socialize their pets",
  "value_proposition": "Connect nearby dog owners to easily schedule and coordinate dog playdates",
  "assumptions": [
    {
      "id": "assumption_1",
      "category": "market",
      "assumption": "Dog owners actively seek playdates and will use an app for this purpose",
      "importance": "critical"
    },
    {
      "id": "assumption_2",
      "category": "user_behavior",
      "assumption": "Users will consistently create profiles and maintain location accuracy",
      "importance": "critical"
    },
    {
      "id": "assumption_3",
      "category": "competition",
      "assumption": "Existing solutions (Facebook groups, Nextdoor, Rover) are inadequate",
      "importance": "important"
    },
    {
      "id": "assumption_4",
      "category": "execution",
      "assumption": "Can achieve critical mass of users in each neighborhood (network effects)",
      "importance": "critical"
    },
    {
      "id": "assumption_5",
      "category": "monetization",
      "assumption": "Users will pay for premium features or tolerate ads",
      "importance": "important"
    },
    {
      "id": "assumption_6",
      "category": "market",
      "assumption": "The problem is painful enough to drive daily/weekly app usage",
      "importance": "critical"
    }
  ],
  "risk_categories": ["market", "user_behavior", "competition", "execution", "monetization"]
}
```

**Note**: The output shows 4 critical assumptions, which exceeds the minimum requirement of 2.

---

## Testing

### Run Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
pytest idea_decomposer/test_decomposer.py -v

# Run specific test class
pytest idea_decomposer/test_decomposer.py::TestInputValidation -v

# Run with coverage
pip install pytest-cov
pytest idea_decomposer/test_decomposer.py --cov=idea_decomposer --cov-report=html
```

### Command Line Testing

```bash
# Test with default example
python -m idea_decomposer.decomposer

# Test with custom idea
python -m idea_decomposer.decomposer "An AI-powered fitness coach for seniors"
```

### Integration Testing (requires API key)

```bash
# Set API key first
export OPENAI_API_KEY="sk-..."

# Run integration tests
pytest idea_decomposer/test_decomposer.py -v -m integration
```

### Manual Testing Checklist

- [ ] Handles valid ideas (50-500 chars)
- [ ] Rejects empty/very short ideas (<10 chars)
- [ ] Rejects very long ideas (>1000 chars)
- [ ] Generates 3-15 assumptions
- [ ] Has at least 2 critical assumptions
- [ ] Assumption IDs are sequential (assumption_1, assumption_2, ...)
- [ ] No duplicate assumption IDs
- [ ] risk_categories matches assumption categories
- [ ] Returns JSON dict by default
- [ ] Can return Pydantic object when requested
- [ ] Error messages are clear and actionable

---

## Integration with Other Modules

### Data Flow in Complete System

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Input                                               │
│    "A social network for dog playdates"                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Idea Decomposer (THIS MODULE)                            │
│    Returns: DecomposedIdea with 6 assumptions               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Knowledge Base Retriever                                 │
│    For each assumption, retrieve counter-evidence           │
│    Input: assumption["assumption"]                          │
│    Output: List[EvidenceItem]                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Reasoning Agent                                          │
│    Critique each assumption with evidence                   │
│    Input: assumption + evidence                             │
│    Output: Critique object                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Final Output                                             │
│    CriticResponse with all critiques + verdict              │
└─────────────────────────────────────────────────────────────┘
```

### Module Dependencies

**This module uses:**
- `common/schemas.py` - Data structures (DecomposedIdea, UserInput, etc.)
- `common/constants.py` - Validation constraints

**Used by:**
- `reasoning/critic_agent.py` - Main agent logic
- `api/app.py` - API endpoints

---

## Error Handling

### Common Errors and Solutions

#### 1. "Prompt template not found"
```
FileNotFoundError: Prompt template not found at idea_decomposer/prompts/idea_decompose.txt
```

**Solution**: 
- Ensure `idea_decompose.txt` exists in `idea_decomposer/prompts/`
- Or specify custom path: `IdeaDecomposer(prompt_path="your/path.txt")`

#### 2. "Idea too short"
```
ValueError: Idea too short. Minimum 10 characters required.
```

**Solution**: Provide more detailed startup idea (at least 10 characters)

#### 3. "Need at least 2 critical assumptions"
```
ValueError: Need at least 2 critical assumptions. Found only 1.
```

**Solution**: 
- This means the LLM didn't generate enough critical assumptions
- Try regenerating (temperature randomness)
- Check your prompt emphasizes "2-3 critical assumptions"

#### 4. "OPENAI_API_KEY not set"
```
openai.error.AuthenticationError: No API key provided
```

**Solution**:
```bash
export OPENAI_API_KEY="sk-..."
```

---

## Troubleshooting

### Issue: LLM generates inconsistent assumption IDs

**Symptom**: IDs like "assum1", "a1", "assumption-1"

**Solution**: The module now auto-corrects these to `assumption_1`, `assumption_2`, etc.

**Code location**: `_validate_assumption_ids()` method

---

### Issue: risk_categories doesn't match assumptions

**Symptom**: 
```json
"assumptions": [...categories: "market", "execution"...],
"risk_categories": ["market", "competition", "timing"]  // Wrong!
```

**Solution**: The module now auto-aligns `risk_categories` to match assumptions

**Code location**: `_validate_risk_categories()` method

---

### Issue: Temperature too high causes unstable output

**Symptom**: Different runs produce vastly different assumption counts or structures

**Solution**: Lower temperature
```python
decomposer = IdeaDecomposer(temperature=0.1)  # More deterministic
```

Recommended: 0.0-0.3 for production, 0.5-0.7 for exploration

---

## Performance Considerations

### API Call Costs

- **Model**: GPT-4o
- **Average tokens per request**: ~500-800 tokens
- **Estimated cost per decomposition**: ~$0.01-0.02

### Latency

- **Average response time**: 2-5 seconds
- **Factors**: Prompt length, temperature, OpenAI API load

### Caching Strategy (future improvement)

Consider caching decompositions for identical ideas:
```python
# Pseudo-code for future enhancement
cache_key = hashlib.md5(idea.encode()).hexdigest()
if cache_key in cache:
    return cache[cache_key]
```

---

## Future Improvements

- [ ] Add caching for duplicate ideas
- [ ] Support for batch processing multiple ideas
- [ ] Multi-language support (non-English ideas)
- [ ] Confidence scores for each assumption
- [ ] Alternative LLM support (Claude, Gemini)
- [ ] Async processing for better performance
- [ ] More granular importance levels (5-point scale)
- [ ] Automatic assumption deduplication logic
- [ ] Export to different formats (CSV, Excel)

---

## Dependencies

### Required Packages

```yaml
# Core dependencies (from environment.yml)
- python>=3.10
- langchain>=0.2.0
- langchain-openai
- openai>=1.0.0
- pydantic>=2.0

# Testing
- pytest
- pytest-mock
- pytest-cov (optional, for coverage)
```

### Installation

```bash
# With conda
conda env create -f environment.yml
conda activate ai-critic-agent

# Or with pip
pip install langchain langchain-openai openai pydantic
```

---

## API Reference

### Class: `IdeaDecomposer`

#### `__init__(model_name, temperature, prompt_path)`
Initialize the decomposer.

**Parameters**:
- `model_name` (str): OpenAI model identifier. Default: `"gpt-4o"`
- `temperature` (float): Temperature for generation. Default: `0.3`
- `prompt_path` (str | None): Custom prompt path. Default: `None` (uses default)

#### `decompose(idea, return_json=True)`
Decompose a startup idea into structured assumptions.

**Parameters**:
- `idea` (str): The startup idea text
- `return_json` (bool): If True, return dict; if False, return `DecomposedIdea` object

**Returns**: `dict` or `DecomposedIdea`

**Raises**:
- `ValueError`: If input is invalid or output doesn't meet constraints
- `RuntimeError`: For unexpected errors

#### `decompose_from_user_input(user_input, return_json=True)`
Convenience method using `UserInput` Pydantic object.

**Parameters**:
- `user_input` (UserInput): Validated user input object
- `return_json` (bool): Return format preference

**Returns**: `dict` or `DecomposedIdea`

---

### Function: `decompose_idea()`

Quick one-liner for decomposition.

```python
def decompose_idea(
    idea: str,
    model_name: str = "gpt-4o",
    temperature: float = 0.3,
    return_json: bool = True
) -> Union[Dict, DecomposedIdea]
```

**Example**:
```python
result = decompose_idea("A marketplace for renting cameras")
```

---

## Best Practices

### 1. Use JSON output for pipeline integration
```python
# For passing to other modules
result = decomposer.decompose(idea, return_json=True)
```

### 2. Use Pydantic objects for type safety
```python
# For internal logic with IDE support
result = decomposer.decompose(idea, return_json=False)
```

### 3. Handle errors gracefully
```python
try:
    result = decomposer.decompose(user_idea)
except ValueError as e:
    print(f"Validation error: {e}")
except RuntimeError as e:
    print(f"System error: {e}")
```

### 4. Keep temperature low for production
```python
# Production: deterministic output
decomposer = IdeaDecomposer(temperature=0.2)

# Exploration: more creative output
decomposer = IdeaDecomposer(temperature=0.6)
```

---

## Contact & Support

**Module Owner**: [Your Name]  
**Team Lead**: [Lead Name]  
**Project Repository**: [GitHub/GitLab URL]

For questions or issues:
1. Check this README first
2. Check `test_decomposer.py` for examples
3. Contact module owner or team lead
4. Open an issue in the project repository

---

## Changelog

### v1.2.0 (2024-12-13) - Current
- ✅ Migrated to Pydantic Structured Output (replaced `json.loads`)
- ✅ Added automatic assumption ID validation and correction
- ✅ Added risk_categories alignment check
- ✅ Enforced minimum 2 critical assumptions requirement
- ✅ Added prompt template validation
- ✅ Improved CLI output handling for Enum types

### v1.1.0 (2024-12-12)
- Added JSON output option
- Improved error messages
- Added comprehensive unit tests

### v1.0.0 (2024-12-11)
- Initial implementation
- Basic decomposition functionality
- Pydantic schema validation

---

## License

[Your License Here]

---

**Remember**: This module is the first step in the AI Critic Agent pipeline. Quality decomposition = better critiques!