
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import engine

from app.api.routes import auth as auth_routes, tutor as tutor_routes
from app.api.routes import students as student_routes, courses as course_routes
from app.api.routes import batches as batch_routes, enrollments as enrollment_routes
from app.api.routes import invoices as invoice_routes, payments as payment_routes, expenses as expense_routes
from app.api.routes import forecast as forecast_routes
from app.api.routes import ai as ai_routes, notifications as notification_routes
from app.api.routes import attendance as attendance_routes, learning as learning_routes
from app.api.routes import parent as parent_routes, account as account_routes
from app.api.routes import chat as chat_routes
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="TeachMan API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routers - unchanged
app.include_router(auth_routes.router)
app.include_router(tutor_routes.router)
app.include_router(student_routes.router)
app.include_router(course_routes.router)
app.include_router(batch_routes.router)
app.include_router(enrollment_routes.router)
app.include_router(invoice_routes.router)
app.include_router(payment_routes.router)
app.include_router(expense_routes.router)
app.include_router(forecast_routes.router)
app.include_router(ai_routes.router)
app.include_router(notification_routes.router)
app.include_router(attendance_routes.router)
app.include_router(learning_routes.router)
app.include_router(parent_routes.router)
app.include_router(account_routes.router)
app.include_router(chat_routes.router)


# Root endpoint
@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "TeachMan API is running"
    }


# Existing health endpoint - unchanged
@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "product": "TeachMan"
    }


# Neon database connection diagnostic
@app.get("/api/db-check")
def db_check():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        current_database(),
                        current_schema(),
                        current_user
                """)
            )

            row = result.fetchone()

            return {
                "status": "connected",
                "database": row[0],
                "schema": row[1],
                "user": row[2]
            }

    except Exception:
        # Do not expose database credentials or internal errors publicly
        return {
            "status": "error",
            "message": "Database connection failed. Check backend logs."
        }
