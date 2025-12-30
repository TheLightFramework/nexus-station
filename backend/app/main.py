from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import audit
from app.api.routes import chat  # Import

# NEW: Lp Live-Patch
from app.lp.manager import LpManager


# 1. Initialize Safe Logging (The Zero-Log Policy)
setup_logging()

# 2. Create the App
app = FastAPI(title=settings.PROJECT_NAME)

# NEW: Create the Lp manager (stored on app.state)
app.state.lp = LpManager(
    versions_url=settings.LP_VERSIONS_URL,
    profile=settings.LP_PROFILE,
    cache_dir=settings.LP_CACHE_DIR,
    timeout_seconds=settings.LP_HTTP_TIMEOUT_SECONDS,
)


# NEW: Load Lp on startup (remote first, fallback to cache)
@app.on_event("startup")
async def load_lp_on_startup():
    await app.state.lp.load()


# 3. Setup CORS (To allow React to talk to Python)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 4. Include the Audit Route
app.include_router(audit.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")  # Include

# NEW: Lp status endpoint
@app.get("/api/v1/lp/status")
def lp_status():
    return app.state.lp.status_dict()

# 5. Health Check Endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "light_meter": "active"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
