# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager, suppress
from backend.api.routes import api_router
from backend.utils.logger import setup_logger

logger = setup_logger("app_main")


def run_monitoring_cycle(human_oversight: bool) -> None:
    """Run one synchronous monitoring pass for every configured region."""
    from backend.agent.agent import DeForestNetAgent
    from backend.database.database import SessionLocal
    from backend.models.alert import RegionOfInterest

    db = SessionLocal()
    try:
        region_names = [region.name for region in db.query(RegionOfInterest).all()]
        if not region_names:
            logger.warning("Scheduled monitoring skipped because no regions are configured.")
            return

        for region_name in region_names:
            try:
                metrics = DeForestNetAgent().run(
                    region_name, db, human_oversight=human_oversight
                )
                logger.info("Scheduled monitoring completed for %s: %s", region_name, metrics)
            except Exception:
                # A failure in one ROI must not prevent checks for the remaining regions.
                logger.exception("Scheduled monitoring failed for region: %s", region_name)
    finally:
        db.close()


async def monitoring_loop(stop_event: asyncio.Event, interval_seconds: int, human_oversight: bool) -> None:
    """Run monitoring immediately, then wait for the configured interval."""
    while not stop_event.is_set():
        await asyncio.to_thread(run_monitoring_cycle, human_oversight)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass

# Lifespan manager to handle startup database initialization and seeding
@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    from backend.config import (
        AGENT_HUMAN_OVERSIGHT,
        AGENT_RUN_ON_STARTUP,
        AGENT_SCAN_INTERVAL_SECONDS,
        AGENT_SCHEDULER_ENABLED,
        SIMULATION_MODE,
    )
    logger.info(f"Starting DeForestNet backend... Simulation Mode: {SIMULATION_MODE}, env value: {repr(os.environ.get('SIMULATION_MODE'))}, cwd: {os.getcwd()}")
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

    scheduler_stop_event = asyncio.Event()
    scheduler_task = None
    if AGENT_SCHEDULER_ENABLED:
        initial_delay = 0 if AGENT_RUN_ON_STARTUP else AGENT_SCAN_INTERVAL_SECONDS

        async def scheduled_monitoring() -> None:
            if initial_delay:
                try:
                    await asyncio.wait_for(scheduler_stop_event.wait(), timeout=initial_delay)
                except asyncio.TimeoutError:
                    pass
            if not scheduler_stop_event.is_set():
                await monitoring_loop(
                    scheduler_stop_event,
                    AGENT_SCAN_INTERVAL_SECONDS,
                    AGENT_HUMAN_OVERSIGHT,
                )

        scheduler_task = asyncio.create_task(scheduled_monitoring())
        logger.info(
            "Continuous monitoring enabled: interval=%ss, human_oversight=%s, run_on_startup=%s",
            AGENT_SCAN_INTERVAL_SECONDS,
            AGENT_HUMAN_OVERSIGHT,
            AGENT_RUN_ON_STARTUP,
        )

    yield
    scheduler_stop_event.set()
    if scheduler_task:
        scheduler_task.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler_task
    logger.info("Shutting down DeForestNet backend...")

# Initialize FastAPI App
app = FastAPI(
    title="DeForestNet API",
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

<<<<<<< Updated upstream
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

=======
@app.get("/")
def read_root():
    """Welcome and metadata endpoint"""
    return {
        "app": "DeForestNet API Backend",
        "status": "Online",
        "sdg_alignment": ["SDG 13: Climate Action", "SDG 15: Life on Land"],
        "api_docs": "/docs"
    }
>>>>>>> Stashed changes
