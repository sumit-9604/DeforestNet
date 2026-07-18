# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.routes import api_router
from backend.utils.logger import setup_logger

logger = setup_logger("app_main")

# Lifespan manager to handle startup database initialization and seeding
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ForestGuard backend...")
    try:
        from backend.database.database import init_db, SessionLocal
        from backend.database.seed import seed_database
        
        logger.info("Initializing database schemas...")
        init_db()
        
        db = SessionLocal()
        try:
            logger.info("Seeding database standard data...")
            seed_database(db)
        finally:
            db.close()
            
    except Exception as e:
        logger.critical(f"Critical failure initializing database: {e}", exc_info=True)
        
    yield
    logger.info("Shutting down ForestGuard backend...")

# Initialize FastAPI App
app = FastAPI(
    title="ForestGuard API",
    description="Autonomous AI Agent Deforestation Detection, Analysis & Reporting System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
# Allows the React frontend to communicate with endpoints from other ports/domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific domains in production (e.g. ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Register API Router
app.include_router(api_router, prefix="/api")

# Serve Frontend static assets in production
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # Mount assets folder for static scripts and CSS
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static")

    # Serve index.html for index and any catch-all routes to support client routing
    @app.get("/")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    @app.get("/{catchall:path}")
    async def serve_fallback(catchall: str):
        # Ensure we don't intercept API endpoints or FastAPI docs
        if catchall.startswith("api") or catchall.startswith("docs") or catchall.startswith("openapi.json"):
            return None
        return FileResponse(str(FRONTEND_DIST / "index.html"))
else:
    @app.get("/")
    def read_root():
        """Welcome and metadata endpoint (dev fallback)"""
        return {
            "app": "ForestGuard API Backend",
            "status": "Online",
            "sdg_alignment": ["SDG 13: Climate Action", "SDG 15: Life on Land"],
            "api_docs": "/docs"
        }

