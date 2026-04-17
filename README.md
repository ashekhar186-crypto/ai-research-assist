# AI Research Assistant

Full-stack research workflow assistant for analyzing papers, generating literature reviews, identifying research gaps, drafting grant proposals, and supporting paper writing.

## Stack

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL
- Queue/Cache: Redis
- AI + Retrieval: Anthropic, LangChain, FAISS, sentence-transformers

## Included In This Repository

This repository is intentionally limited to professional project essentials:

- application source code
- dependency manifests
- Docker setup
- environment template
- minimal project documentation

Generated assets, local databases, uploaded papers, indexes, virtual environments, reports, presentation files, and personal working documents are excluded from version control.

## Project Structure

```text
backend/    FastAPI API, agents, models, database, and tools
frontend/   React application built with Vite
```

## Local Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000` and proxies API calls to `http://localhost:8000`.

## Docker

```bash
docker compose up --build
```

This starts:

- PostgreSQL on `5432`
- Redis on `6379`
- FastAPI backend on `8000`

## Environment Variables

Copy [`.env.example`](/Users/ashishshekhar/ai-research-assistant/.env.example) to `backend/.env` for local development and replace placeholder values before running the app.

Important variables include:

- `ANTHROPIC_API_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `FRONTEND_URL`
- `BACKEND_URL`

## Notes

- Do not commit real `.env` files or API keys.
- Do not commit generated uploads, local databases, or FAISS indexes.
- If any credentials were previously stored locally, rotate them before publishing the repo.
