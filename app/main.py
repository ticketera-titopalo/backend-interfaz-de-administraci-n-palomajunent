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

# Rate limiter configuration
# Using in-memory storage (use Redis in production for better performance)
# RATE_LIMIT_LOGIN: 5 attempts per minute per IP
# RATE_LIMIT_REFRESH: 3 attempts per hour per IP
# RATE_LIMIT_PURCHASES: 10 requests per hour per user
rate_limit_storage = {}
RATE_LIMIT_LOGIN = 5  # 5 intentos por minuto
RATE_LIMIT_REFRESH = 3  # 3 intentos por hora
RATE_LIMIT_PURCHASES = 10  # 10 requests por hora por usuario

app = FastAPI(
    title="Ticketera - Admin API",
    version="1.0.0",
    description="""
    # Ticketera - Interfaz de Administración
    
    API REST para la gestión administrativa de la plataforma Ticketera.
    
    ## Características
    - **Autenticación JWT** - Sistema de login/refresh/logout con tokens seguros
    - **CRUD completo** - Conciertos, usuarios, tickets y compras
    - **Validación de stock** - Control en tiempo real de disponibilidad
    - **Emisión de tickets** - Generación de códigos QR únicos
    - **Rate limiting** - Protección contra abusos de endpoints
    - **Seguridad headers** - Headers HTTP para protección contra XSS, Clickjacking, etc.
    
    ## Authentication
    La mayoría de los endpoints requieren autenticación JWT mediante header `Authorization: Bearer <token>`.
    - Login: `POST /api/login` con email y contraseña
    - Refresh token: `POST /api/refresh` para renovar tokens
    - Logout: `POST /api/logout`
    
    ## Versioning
    Versión actual: 1.0.0
    """,
    terms_of_service="https://ticketera.com/terms",
    contact={
        "name": "Ticketera Development Team",
        "email": "dev@ticketera.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    # Rutas personalizadas para documentación
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
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
    """Verificar límite de tasa para una clave dada.
    
    Args:
        key: Identificador único para el límite (ej. IP, usuario ID).
        limit: Número máximo de allowed requests.
        period: Ventana de tiempo en segundos para el límite.
    
    Returns:
        bool: True si el request está dentro del límite, False si se excedió.
    
    Note:
        Este es un rate limiter simple en memoria. Para producción,
        se recomienda usar Redis o una solución dedicada de rate limiting.
    """
    now = time.time()
    if key not in rate_limit_storage:
        rate_limit_storage[key] = []
    
    # Limpiar entradas viejas fuera de la ventana de tiempo
    rate_limit_storage[key] = [t for t in rate_limit_storage[key] if now - t < period]
    
    if len(rate_limit_storage[key]) >= limit:
        return False
    
    rate_limit_storage[key].append(now)
    return True

# Handler global para HTTPExceptions
"""
Handler personalizado para excepciones HTTP de FastAPI.

Convierte todas las HTTPException en respuestas JSON consistentes
con la estructura: {'error': {'type': 'ExceptionName'}, 'detail': 'mensaje'}.

Esta handler asegura que todos los errores de la API tengan un formato
estándar, facilitando el consumo por parte de front-ends y clientes API.
"""
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
    """Endpoint de salud de la API (público, sin auth requerido).
    
    Returns status 'ok' indicando que la API está operativa y conectada.
    Este endpoint no requiere autenticación JWT y puede ser usado por:
    - Sistemas de monitoreo (health checks)
    - Load balancers para routing
    - Verificación de disponibilidad del servicio
    
    Returns:
        dict: {'status': 'ok'}
    
    Example:
        >>> import requests
        >>> r = requests.get('http://localhost:5001/api/health')
        >>> r.json()  # {'status': 'ok'}
    """
    return {"status": "ok"}
