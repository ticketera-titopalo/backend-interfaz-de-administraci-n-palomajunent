# backend-interfaz-de-administraci-n-palomajunent
interfaz de admin del backend

## Infraestructura FastAPI
Este proyecto utiliza FastAPI para la API de administración.

### Dependencias
fastapi, uvicorn, python-jose, passlib, sqlalchemy, asyncmy, python-dotenv

### Variables de entorno (.env)
Copiar .env.example y configurar:
- DATABASE_URI: Cadena de conexión a MySQL
- SECRET_KEY: Clave secreta para JWT
- PORT: Puerto del servidor (5001)
- CORS_ORIGINS: Origen del front cliente (http://localhost:5173)

### Levantar el servidor
```bash
uvicorn app.main:app --port 5001
```

### Endpoints
- `GET /api/health` - Verificar estado de la API (200 OK)
