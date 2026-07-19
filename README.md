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

The root Compose file runs the complete local stack. Production uses separate deployment units:

- Render must deploy the backend from the repository Blueprint in `render.yaml`. The service is Docker-based, with `backend` as both its root directory and Docker build context. Do not create it as a native auto-detected service at the repository root, or Railpack will see both applications and fail to choose a build.
- Vercel must deploy the `frontend` directory. Configure the Vercel project environment variable `VITE_BACKEND_URL` to the public Render backend URL, for example `https://vc-brain-backend.onrender.com`.

The frontend GitHub Actions workflow requires these repository Actions secrets:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

The workflow now stops with a clear error if any of these values is missing. Render still requires `MONGODB_URI` and the optional integration API keys to be configured in the service environment.

