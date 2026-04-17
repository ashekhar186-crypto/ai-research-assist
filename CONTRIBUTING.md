# Contributing Guide

Thanks for contributing to AI Research Assistant.

## Development Workflow

1. Create a feature branch from `main`
2. Keep changes focused on a single improvement or fix
3. Update documentation when setup, behavior, or developer workflow changes
4. Run the relevant local checks before opening a pull request
5. Open a pull request with a clear summary and testing notes

## Local Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Suggested Checks

Run the checks relevant to your change:

```bash
cd frontend && npm run build
cd backend && python -m compileall app
```

## Pull Request Expectations

- describe the user-facing or developer-facing change clearly
- include any setup, migration, or environment updates
- mention what you tested locally
- keep unrelated file churn out of the PR

## Secrets and Data

- do not commit `.env` files
- do not commit API keys or credentials
- do not commit uploaded documents, local databases, or generated indexes

## Documentation

If your change affects onboarding or usage, update:

- `README.md`
- `CONTRIBUTING.md`
- environment examples or setup commands when needed
