# VC Brain

VC Brain is a full-stack monorepo for an autonomous venture workflow designed to move from sourcing to a $100K investment decision within 24 hours.

The repository has two intentionally separate deployment units:

- `frontend/`: TanStack Start + React + TypeScript, containerized as a Node/Nitro runtime.
- `backend/`: FastAPI intelligence, memory, and media modules, containerized with Python and uv.

MongoDB runs in Compose with the named `mongodb-data` volume. Configure the optional API keys in `.env` for research, intelligence, and media integrations.

## Quick start

1. Copy local environment files:

   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env
   ```

2. Start the frontend, backend, and MongoDB services:

   ```bash
   docker compose up --build
   ```

Local endpoints:

- Frontend: `http://localhost:3000`
- FastAPI/OpenAPI: `http://localhost:9000/docs`
- MongoDB: `mongodb://localhost:27017`

MongoDB runs in Compose with the named `mongodb-data` volume. Configure the optional API keys in `.env` for research, intelligence, and media integrations.

## Development commands

```bash
cd frontend && npm run build
cd backend && uv sync --all-groups && uv run pytest
cd backend && uv run ruff check .
```

All Python dependency changes must use `uv add`, `uv remove`, or `uv lock`; do not add pip requirements files.

## Deployment

The root Compose file runs the complete local stack. For separate deployments, Render can build `backend/Dockerfile`, while the frontend can use `frontend/Dockerfile` with `VITE_BACKEND_URL` supplied as a build argument.

