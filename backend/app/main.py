from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .config import get_settings
from .routes import auth, clinics, appointments, admin, queue, websocket, analytics, super_admin

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=None,  # Disable default docs
    redoc_url=None
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://apna-bhagalpur-1.onrender.com",
        "https://apna-bhagalpur.onrender.com",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Swagger - only accessible with admin token
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=settings.app_name + " - API Docs",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(title=settings.app_name, version=settings.app_version, routes=app.routes)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clinics.router, prefix="/api/clinics", tags=["Clinics"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(queue.router, prefix="/api/queue", tags=["Queue"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(super_admin.router, prefix="/api/super-admin", tags=["Super Admin"])
app.include_router(websocket.router, tags=["WebSocket"])

@app.get("/")
@limiter.limit("10/minute")
async def root(request: Request):
    return {"app": settings.app_name, "status": "running"}

@app.get("/api/health")
@limiter.limit("60/minute")
async def health(request: Request):
    return {"status": "healthy"}