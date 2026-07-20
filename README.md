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

The root Compose file is for local development only. Railway deploys the monorepo as three independent services:

1. Create a MongoDB service from Railway's MongoDB template. Use its generated connection URL as the backend `MONGODB_URI`.
2. Create a backend service from this repository with root directory `/backend`. Railway will use `backend/Dockerfile`; set `APP_ENV=production`, `MONGODB_DATABASE=vc-brain`, `CORS_ORIGINS` to the public frontend URL, and the optional integration API keys. The backend `PORT` is supplied by Railway.
3. Create a frontend service from this repository with root directory `/frontend`. Railway will use `frontend/Dockerfile`; set `VITE_BACKEND_URL` to the public backend URL. This is a build-time variable and must be present before the frontend deploy is built.

For services created through the Railway dashboard, set the config file path explicitly to `/backend/railway.toml` and `/frontend/railway.toml`. Railway's config file is relative to the repository root even when a service root directory is configured.

The GitHub Actions workflows run CI checks and Docker builds only. Railway handles deployment independently for each service, so local `docker compose up --build` remains unchanged as the local workflow.

