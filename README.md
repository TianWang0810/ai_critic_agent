# AI Critic Agent

LLM-driven venture evaluation system that critiques startup ideas by decomposing proposals and validating them against historical failure patterns across risk dimensions.

## How it works

```
Startup Idea
    │
    ▼ IdeaDecomposer (LangChain + GPT-4)
5–8 Structured Assumptions
    │
    ▼ CriticKnowledgeBase (FAISS semantic search, sub-20ms)
Historical failure evidence per assumption
    │
    ▼ CriticAgent critique_chain (LangChain LCEL)
Per-assumption critique with risk level
    │
    ▼ CriticAgent verdict_chain (LangChain LCEL)
Final verdict + success probability
    │
    ▼ PostgreSQL (SQLAlchemy)
Persisted for historical analysis
```

## Stack

- **LLM**: GPT-4o via LangChain (`ChatOpenAI`, LCEL chains, `JsonOutputParser`)
- **Vector search**: FAISS (`IndexFlatIP`) over 27 curated startup failure case studies
- **Embeddings**: `all-MiniLM-L6-v2` (sentence-transformers, 384-dim)
- **API**: FastAPI — deployable to AWS Lambda via Mangum
- **Storage**: PostgreSQL (SQLAlchemy 2.0), SQLite fallback for local dev
- **Validation**: Pydantic v2

## Setup

```bash
conda env create -f ai_critic_agent/environment.yml
conda activate ai-critic-agent

# Build FAISS index (first time only)
cd ai_critic_agent
python -m knowledge_base.ingest.build_index
```

## Usage

### CLI
```bash
cd ai_critic_agent
python main.py
# or pass idea directly
python main.py "A subscription box for pet owners"
```

### API server
```bash
cd ai_critic_agent
python api/app.py
# POST http://localhost:8000/api/v1/critique
# GET  http://localhost:8000/api/v1/evaluations
```

### Python
```python
from reasoning.critic_agent import CriticAgent
from common.schemas import EvaluationConfig

agent = CriticAgent(config=EvaluationConfig(
    focus_categories=["market", "competition"],
    evidence_count=5,
))
response = agent.critique_idea("A social network for dog owners")
print(response.verdict.overall_risk)
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | Model override (default: `gpt-4o`) |
| `DATABASE_URL` | No | PostgreSQL URL (default: SQLite fallback) |

## Knowledge base

27 curated startup failure case studies across 7 risk categories: market, competition, execution, monetization, user_behavior, timing, general.

To add new cases: drop a `.md` file into `ai_critic_agent/knowledge_base/data/<category>/` and re-run `build_index.py`.
