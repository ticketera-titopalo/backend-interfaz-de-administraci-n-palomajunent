from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Importar routers
from app.routes.concerts import router as concerts_router
from app.routes.users import router as users_router
from app.routes.tickets import router as tickets_router
from app.routes.auth import router as auth_router
from app.routes.purchases import router as purchases_router

# Simple rate limiter en memoria (usar Redis en producción)
rate_limit_storage = {}
RATE_LIMIT_LOGIN = 5  # 5 intentos por minuto
RATE_LIMIT_REFRESH = 3  # 3 intentos por hora
RATE_LIMIT_PURCHASES = 10  # 10 requests por hora por usuario

app = FastAPI(
    title="Ticketera - Admin API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para añadir headers de seguridad
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Rate limiter helper
def check_rate_limit(key, limit, period):
    """Verificar límite de tasa para una clave dada."""
    now = time.time()
    if key not in rate_limit_storage:
        rate_limit_storage[key] = []
    
    # Limpiar entradas viejas
    rate_limit_storage[key] = [t for t in rate_limit_storage[key] if now - t < period]
    
    if len(rate_limit_storage[key]) >= limit:
        return False
    
    rate_limit_storage[key].append(now)
    return True

# Handler global para HTTPExceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"type": exc.__class__.__name__},
            "detail": exc.detail
        }
    )

# Incluir routers de la API
app.include_router(concerts_router)
app.include_router(users_router)
app.include_router(tickets_router)
app.include_router(auth_router)
app.include_router(purchases_router)

@app.get("/api/health", tags=["health"])
def health_check():
    """Endpoint de salud de la API (público, sin auth requerido)."""
    return {"status": "ok"}
