from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routes import auth, clinics, appointments, admin, queue, websocket, analytics, super_admin

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clinics.router, prefix="/api/clinics", tags=["Clinics"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(queue.router, prefix="/api/queue", tags=["Queue"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(super_admin.router, prefix="/api/super-admin", tags=["Super Admin"])
app.include_router(websocket.router, tags=["WebSocket"])

@app.get("/")
async def root():
    return {"app": settings.app_name, "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}