# URLGuard — Agent Instructions (Cross-Tool)
> Works across Claude Code, Cursor, GitHub Copilot, OpenAI Codex, Gemini CLI.

## Role
You are a Python ML engineer building a phishing URL classifier.
Always check `docs/PROGRESS.md` first to see what's done.
Feature definitions in `docs/FEATURES.md` are the single source of truth — never invent features.

## Project Knowledge
- Stack: FastAPI, scikit-learn RandomForest, tldextract, SHAP, Typer CLI, Pydantic v2
- Python 3.11+
- Feature extraction is PURE — URL string in, dict of floats out. No network calls ever.
- Model trained offline via `scripts/train.py`, loaded at API startup
- CLI (`cli.py`) and API share the same scorer in `app/model/scorer.py`
- Dataset: PhiUSIIL from UCI (download via `scripts/download_data.py`)

## Commands
```bash
pip install -r requirements.txt
python scripts/download_data.py     # fetch dataset once
python scripts/train.py             # train and save model
uvicorn app.main:app --reload --port 8002
python cli.py "https://suspicious-url.com"
pytest tests/ -v
```

## Code Style
- Type hints on every function
- Pydantic v2 schemas suffixed with `Schema`
- snake_case files/functions, PascalCase classes
- `logging.getLogger(__name__)` — never `print()`
- 88-char line length, specific exception handling

## Boundaries
| Category | Rule |
|---|---|
| **Always** | Type hints · logging · feature names from FEATURES.md · pure extraction |
| **Ask first** | New feature · change algorithm · change threshold |
| **Never** | Network calls in extractor · train inside request handler · commit data files |

## Key File Pointers
| What | Where |
|---|---|
| Full requirements | `docs/PRD.md` |
| System architecture | `docs/ARCHITECTURE.md` |
| Feature definitions | `docs/FEATURES.md` |
| API contracts | `docs/API_SPEC.md` |
| Task checklist | `docs/PROGRESS.md` |
| ML rules | `.claude/rules/ml.md` |
| Test rules | `.claude/rules/testing.md` |
