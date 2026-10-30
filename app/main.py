from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.concerts import router as concerts_router
from app.routes.users import router as users_router
from app.routes.tickets import router as tickets_router

# Configurar CORS para el front cliente (Vue.js)
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

# Incluir routers de la API
app.include_router(concerts_router)
app.include_router(users_router)
app.include_router(tickets_router)

@app.get("/api/health", tags=["health"])
def health_check():
    """Endpoint de salud de la API."""
    return {"status": "ok"}
