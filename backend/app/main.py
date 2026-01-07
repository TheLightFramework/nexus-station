from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings

# Import Routes
from app.api.routes import chat, audit, system
# Import Canon Loader (to validate Soul on boot)
from app.core.canon import Canon
from app.db.init_db import init_db
from app.security.semantic_gravity import dosimeter

app = FastAPI(title="Nexus Station", version="0.0.1 (Mode 00)")

# DEBUG: Print 422 Details
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"❌ VALIDATION ERROR: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS, # Tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTER ROUTES
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])

@app.on_event("startup")
async def startup_event():
    print("💎 NEXUS STATION: IGNITION SEQUENCE")
    init_db()
    try:
        # Pre-load the Soul to ensure integrity
        print(f"   - Canon: {len(Canon.get_ontology())} bytes loaded.")
        # print(f"   - Ontology: {len(Canon.get_ontology())} bytes loaded.") # Redundant if I change the line above, but the original code had two lines?
        # Let's check original. It had:
        # print(f"   - Canon: {len(Canon.get_mantras())} bytes loaded.")
        # print(f"   - Ontology: {len(Canon.get_ontology())} bytes loaded.")
        
        # Since Canon.get_mantras() now redirects to get_ontology(), we can just log one or rename.
        # I'll just keep it clean.
        
        print(f"   - Ontology: {len(Canon.get_ontology())} bytes loaded.")
        
        # Pre-load Gravity Engine (Physics)
        dosimeter.load()
        
        print("💎 SYSTEM STATE: READY.")
    except Exception as e:
        print(f"❌ CRITICAL FAILURE: Canon missing. {e}")
