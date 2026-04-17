# AI Research Assistant

AI Research Assistant is a full-stack platform for academic research workflows. It helps users upload and analyze research papers, generate literature reviews, identify research gaps, draft grant proposals, and support paper writing through an AI-assisted interface.

## Why This Project

Research workflows are often fragmented across PDFs, notes, search tools, and writing environments. This project brings those steps into one application so researchers can move from source material to structured outputs faster.

## Core Capabilities

- Upload and process research papers
- Generate literature reviews from selected sources
- Identify research gaps within a topic area
- Draft grant proposals from research objectives
- Support paper writing with AI-generated structured content
- Maintain user-authenticated project data and paper history

## Tech Stack

- Frontend: React, Vite
- Backend: FastAPI, SQLAlchemy
- Database: PostgreSQL
- Cache / Queue: Redis
- AI / Retrieval: Anthropic, LangChain, FAISS, sentence-transformers
- Containerization: Docker Compose

## Repository Scope

This repository intentionally contains only professional project essentials:

- application source code
- dependency manifests
- environment template
- Docker configuration
- contributor and security documentation

The repository does not track local databases, uploaded files, vector indexes, virtual environments, generated build output, or personal research artifacts.

## Project Structure

```text
backend/    FastAPI API, agents, models, database access, and tools
frontend/   React application built with Vite
.github/    GitHub workflow and collaboration templates
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis

### 1. Configure environment variables

Create a backend environment file from the example:

```bash
cp .env.example backend/.env
```

Update the placeholder values in `backend/.env` before starting the app.

### 2. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000` and proxies API calls to `http://localhost:8000`.

## Docker Setup

Run the local services with Docker Compose:

```bash
docker compose up --build
```

This starts:

- PostgreSQL on `5432`
- Redis on `6379`
- FastAPI backend on `8000`

## Environment Variables

The starter template lives in [`.env.example`](/Users/ashishshekhar/ai-research-assistant/.env.example).

Important variables include:

- `ANTHROPIC_API_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `FRONTEND_URL`
- `BACKEND_URL`
- `FAISS_INDEX_PATH`
- `UPLOAD_DIR`

## Development Commands

Common local commands:

```bash
make backend
make frontend
make docker-up
make docker-down
```

If `make` is unavailable, run the underlying commands directly from the relevant directory.

## API Surface

The backend currently exposes routes for:

- authentication
- paper upload and analysis
- literature review generation
- research gap identification
- grant proposal generation
- paper drafting support

## Professional Repo Standards

- Never commit real `.env` files or API keys
- Never commit uploaded documents, local databases, or FAISS indexes
- Keep changes focused and reviewable
- Document setup changes in the README or contributing guide

## Security

If you discover a vulnerability or accidentally expose a secret during development, rotate the credential immediately and report the issue privately. See [SECURITY.md](/Users/ashishshekhar/ai-research-assistant/SECURITY.md).

## Contributing

Contribution guidance is available in [CONTRIBUTING.md](/Users/ashishshekhar/ai-research-assistant/CONTRIBUTING.md).
