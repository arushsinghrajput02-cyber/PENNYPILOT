import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.database import Base, engine
from backend.routers import auth, transactions, budgets, goals, challenges, analytics, demo

# Create database tables automatically upon startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PennyPilot — Smart Student Finance Platform API (B.Tech CSE Project)",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(budgets.router, prefix=settings.API_V1_STR)
app.include_router(goals.router, prefix=settings.API_V1_STR)
app.include_router(challenges.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)

# Frontend Path resolution
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

if frontend_dir.exists():
    # Mount static assets for CSS, JS, etc.
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")

    # Serve HTML page routes
    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")

    @app.get("/login", include_in_schema=False)
    @app.get("/login.html", include_in_schema=False)
    async def serve_login():
        return FileResponse(frontend_dir / "login.html")

    @app.get("/register", include_in_schema=False)
    @app.get("/register.html", include_in_schema=False)
    async def serve_register():
        return FileResponse(frontend_dir / "register.html")

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/dashboard.html", include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(frontend_dir / "dashboard.html")

    @app.get("/transactions", include_in_schema=False)
    @app.get("/transactions.html", include_in_schema=False)
    async def serve_transactions():
        return FileResponse(frontend_dir / "transactions.html")

    @app.get("/budgets", include_in_schema=False)
    @app.get("/budgets.html", include_in_schema=False)
    async def serve_budgets():
        return FileResponse(frontend_dir / "budgets.html")

    @app.get("/analytics", include_in_schema=False)
    @app.get("/analytics.html", include_in_schema=False)
    async def serve_analytics():
        return FileResponse(frontend_dir / "analytics.html")

    @app.get("/goals", include_in_schema=False)
    @app.get("/goals.html", include_in_schema=False)
    async def serve_goals():
        return FileResponse(frontend_dir / "goals.html")

    @app.get("/challenges", include_in_schema=False)
    @app.get("/challenges.html", include_in_schema=False)
    async def serve_challenges():
        return FileResponse(frontend_dir / "challenges.html")


@app.get("/api/health")
def health_check():
    """Service health status endpoint."""
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
