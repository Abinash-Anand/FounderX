# VC Brain

VC Brain is a full-stack monorepo for an autonomous venture workflow designed to move from sourcing to a $100K investment decision within 24 hours.

The repository has two intentionally separate deployment units:

- `frontend/`: TanStack Start + React + TypeScript, deployed natively to Vercel (never containerized).
- `backend/`: FastAPI intelligence, memory, and media modules, deployed as a lean Docker image to Render.

MongoDB Atlas is now the persistence target for founder, memo, and signal records. The root Compose stack is no longer used for the primary database workflow.

## Quick start

1. Copy local environment files:

   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env
   ```

2. Start the local backend and any optional supporting services:

   ```bash
   docker compose up --build
   ```

3. Start the frontend on the host (it is deliberately not part of Compose):

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

Local endpoints:

- Frontend: `http://localhost:3000`
- FastAPI/OpenAPI: `http://localhost:8080/docs`
- MongoDB: `mongodb://localhost:27017`

The Compose stack no longer provisions the primary data plane. Configure `MONGODB_URI` and `MONGODB_DATABASE` for the backend to connect to Atlas or a local MongoDB instance.

## Development commands

```bash
cd frontend && npm run build
cd backend && uv sync --all-groups && uv run pytest
cd backend && uv run ruff check .
```

All Python dependency changes must use `uv add`, `uv remove`, or `uv lock`; do not add pip requirements files.

## Deployment

Connect `frontend/` as the Vercel project root. Render can consume `render.yaml` or build `backend/Dockerfile` with `backend/` as its Docker context. Configure the secrets documented in each deployment unit's `.env.example`.

