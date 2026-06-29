# Zomato AI Restaurant Recommender

AI-powered restaurant recommendation service inspired by Zomato. Combines structured filtering over a real-world Zomato dataset with Groq LLM reasoning to produce personalized, explainable recommendations.

## Prerequisites

- Python 3.10+
- [Groq API key](https://console.groq.com/)

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# Edit .env and add your GROQ_API_KEY
```

## Verify installation

```bash
python -c "from app.config import settings; print(settings.llm_model)"
pytest tests/test_config.py tests/test_preprocessor.py tests/test_store.py tests/test_filters.py -v
```

Expected output: `llama-3.3-70b-versatile` and passing tests.

## Load dataset (Phase 1)

```bash
python -c "from app.data import get_restaurant_store; s = get_restaurant_store(); print(s.count, 'restaurants'); print('Locations:', len(s.get_locations()))"
```

First run downloads from Hugging Face and caches to `data/cache/restaurants.parquet`. Subsequent runs load from cache.

## Project structure

```
├── app/
│   ├── config.py           # Environment configuration
│   ├── models/             # Data models
│   ├── data/               # Dataset loading & preprocessing
│   ├── filters/            # Preference parsing & filtering
│   ├── llm/                # Groq integration
│   └── services/           # Recommendation orchestration
├── ui/                     # Streamlit UI (Phase 5)
├── tests/                  # Unit & integration tests
├── data/cache/             # Cached dataset (gitignored)
└── Docs/                   # Architecture & planning docs
```

## Documentation

- [Context](./Docs/context.md)
- [Architecture](./Docs/architecture.md)
- [Implementation plan](./Docs/implementation-plan.md)
- [Edge cases](./Docs/edge-case.md)
- [Dataset schema](./Docs/dataset-schema.md)

## Status

**Phase 2 complete** — preference parsing and deterministic filter engine with progressive relaxation.

Next: [Phase 3 — Groq LLM Layer](./Docs/implementation-plan.md#phase-3-groq-llm-layer)
