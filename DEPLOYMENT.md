# TeachMan Deployment Guide (Render + Neon, Windows)

This guide uses Command Prompt (cmd.exe) on Windows.

## a. Overview

- **Neon** hosts the PostgreSQL database.
- **Render** hosts the FastAPI backend (a web service) and the React frontend (a static site).
- The frontend uses `VITE_API_BASE_URL` for the backend in production and `/api` through the local Vite proxy during development.

## b. Step 1 — Neon database

1. Sign up at https://neon.tech.
2. Create a project. Choose a region near your users.
3. Copy the connection string from the Neon dashboard.
4. Change the leading `postgresql://` to `postgresql+psycopg://` and keep `?sslmode=require` at the end.

Shape only (do not use this literal text):

```
postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

Never commit this URL. It contains your database password.

## c. Step 2 — Migrate Neon (before deploying)

Run these in Command Prompt, from the `backend\` folder, with the virtual environment active.

1. Open `backend\.env` and set the `DATABASE_URL` line to the Neon URL from Step 1.
2. Regenerate the migration on the **empty** Neon database:

```
del migrations\versions\0001_initial.py
python -m alembic revision --autogenerate -m "initial schema"
python -m alembic upgrade head
```

3. Confirm the new migration file contains `cash_snapshots`. Open the new file in `backend\migrations\versions\` and search for `cash_snapshots`.
4. Optional demo data:

```
python -m app.seed
```

The seed creates demo accounts only. Never seed production with real customer data.

## d. Step 3 — Push to GitHub

1. Create a new repository on GitHub.
2. In the project root (the folder that contains `backend\` and `frontend\`), run:

```
git init
git add .
git commit -m "TeachMan initial"
git remote add origin <url>
git push -u origin main
```

Replace `<url>` with your repository URL.

3. Run `git status`. Confirm `.env` does **not** appear in the list. The `.gitignore` file should exclude it.

## e. Step 4 — Render blueprint

1. In the Render dashboard, choose **New > Blueprint**.
2. Connect your GitHub repository.
3. Render reads `render.yaml` and creates two services: `teachman-api` and `teachman-web`.
4. Fill in the prompted secrets:
   - `DATABASE_URL` — the Neon URL (with `postgresql+psycopg://`).
   - `NVIDIA_API_KEY` — your NVIDIA API key.
   - `CORS_ORIGINS` — the `teachman-web` URL, for example `https://teachman-web.onrender.com`.
5. Set `VITE_API_BASE_URL` on the `teachman-web` service to the deployed backend URL, for example `https://teachman-api.onrender.com`. The frontend adds the `/api` route prefix exactly once.

## f. Step 5 — Verify

1. Open `https://<api>/api/health`. It should report that the service is up.
2. Open `https://<api>/docs`. You should see the API documentation page.
3. Open the frontend URL (the `teachman-web` URL).
4. Log in with a registered account.
5. Test the support chat bubble.
6. Open the tutor **Assistant** page and test the analytics chat.

## g. Environment variables

| Name | Where it is set | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | Render (`teachman-web`), prompted | Deployed FastAPI backend URL, for example `https://teachman-api.onrender.com` |
| `DATABASE_URL` | Render (`teachman-api`), prompted at blueprint creation | Neon PostgreSQL connection string, in the form `postgresql+psycopg://...?sslmode=require` |
| `JWT_SECRET` | Render, generated automatically (`generateValue`) | Signs login tokens. Must be long and random. |
| `JWT_EXPIRE_MINUTES` | `render.yaml` (value `720`) | How long a login token stays valid, in minutes. |
| `CORS_ORIGINS` | Render (`teachman-api`), prompted | Allowed browser origins for the API, for example the frontend URL. |
| `NVIDIA_API_KEY` | Render (`teachman-api`), prompted | Authenticates calls to the NVIDIA API. Keep secret. |
| `NVIDIA_BASE_URL` | `render.yaml` (`https://integrate.api.nvidia.com/v1`) | NVIDIA API endpoint. |
| `NVIDIA_MODEL` | `render.yaml` (`nvidia/nemotron-3.5-lightning-30b-a3b`) | Model used for the chat features. |
| `NVIDIA_MAX_TOKENS` | `render.yaml` (`4096`) | Maximum tokens in a model reply. |
| `NVIDIA_REASONING_BUDGET` | `render.yaml` (`2048`) | Token budget for the model's reasoning. |
| `NVIDIA_ENABLE_THINKING` | `render.yaml` (`true`) | Turns on the model's thinking mode. |
| `NVIDIA_TIMEOUT_SECONDS` | `render.yaml` (`60`) | How long to wait for an NVIDIA reply before failing. |
| `PYTHON_VERSION` | `render.yaml` (`3.11.9`) | Python version Render uses to build the backend. |

## h. Local run

Backend (in `backend\`, with the virtual environment active):

```
python -m uvicorn app.main:app --reload --port 8000
```

Frontend (in `frontend\`):

```
npm run dev
```

Vite proxies `/api` requests to port 8000.

## i. Security notes

- Never commit `.env` or API keys.
- Rotate any key that was pasted into chat or into a repository.
- Passwords are hashed with Argon2.
- Use a long random `JWT_SECRET`. Render generates one for you.
- The AI never computes money. It receives facts from the database only.
- The support chat stores nothing. Its messages exist only in the current session.

## j. Troubleshooting

- **"password authentication failed"**: `DATABASE_URL` is wrong, or it still points at localhost. Check that the scheme is `postgresql+psycopg://` and that the password matches Neon.
- **"relation does not exist"**: migrations were not run on Neon. Run `python -m alembic upgrade head` against the Neon URL.
- **CORS errors in the browser**: `CORS_ORIGINS` does not contain the frontend URL. Add it and redeploy.
- **Slow first request**: free Render services sleep after inactivity. The first request after a sleep is slow.
- **404 on `/` of the API**: this is normal. Use `/docs` instead.

## k. Cost notes

- Neon and Render free tiers have limits. Check their current pricing pages before you rely on them.
- NVIDIA API usage is billed according to your NVIDIA account.
