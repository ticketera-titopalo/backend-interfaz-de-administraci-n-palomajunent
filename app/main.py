from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configurar CORS para el front cliente
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

@app.get("/api/health", tags=["health"])
def health_check():
    """Endpoint de salud de la API."""
    return {"status": "ok"}
