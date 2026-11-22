TEACHMAN
========

TeachMan is a web app for private tutors and their students' parents. The tutor manages students, courses, batches, enrollments, invoices, payments, expenses and cash forecasts, while parents see their children's classes, fees, attendance and learning progress and can submit UPI payment claims.

STATUS
------

Built and written:
- Backend auth
- Tutor profile
- Students, courses and batches
- Enrollments; approving an enrollment creates an invoice
- Invoices
- Manual payments and parent UPI claims, which the tutor approves
- Expenses
- 30/60/90-day cash forecast with opening cash, plus a what-if simulator that writes nothing
- AI endpoints (uses NVIDIA if NVIDIA_API_KEY is set, template text otherwise)
- Notifications
- Attendance
- Learning progress
- Parent children and dashboard
- Account settings and two-step account deactivation (no financial rows are deleted)
- Seed script
- React frontend pages

NOT YET TESTED. Nothing has been run. The Alembic migration 0001 was hand-written and predates the cash_snapshots table and later changes, so regenerate it with `python -m alembic revision --autogenerate` against a real database before use.

REQUIREMENTS
------------

- Python 3.11+
- Node 20+
- PostgreSQL (Neon)

BACKEND SETUP (Windows PowerShell)
----------------------------------

  cd backend
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install -r requirements.txt
  copy .env.example to .env and set DATABASE_URL, JWT_SECRET, CORS_ORIGINS (optional: NVIDIA_API_KEY)
  python -m alembic upgrade head
  python -m app.seed
  python -m uvicorn app.main:app --reload --port 8000

FRONTEND SETUP (PowerShell)
---------------------------

  cd frontend
  npm install
  npm run dev

Then open http://localhost:5173

DEMO LOGINS
-----------

Password for all accounts: Demo@1234

- Tutor:  phone 9800000001
- Parent: phone 9800000002 (Lakshmi Iyer, child Arjun Iyer)
- Parent: phone 9800000003 (Suresh Menon, child Meera Menon)

NOTES
-----

- Money is stored as integer paise (1 rupee = 100 paise). Rupee inputs are converted when saved.
- API docs are available at http://localhost:8000/docs once the backend is running.
- Never commit .env or API keys.

DEPLOYMENT
----------

- Backend: Render web service, root directory "backend", start command:
    python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
- Database: Neon PostgreSQL
- Frontend: Render static site, root directory "frontend", build command "npm run build", publish directory "dist"
