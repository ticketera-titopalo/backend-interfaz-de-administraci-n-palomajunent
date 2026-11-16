<!-- calidad:inicio -->
![Calidad](https://img.shields.io/badge/Calidad-89%2F100-green) ![Aprobado](https://img.shields.io/badge/Aprobado-SI-green) ![Cumple](https://img.shields.io/badge/Cumple-14%2F15-green) ![Duplicación](https://img.shields.io/badge/Duplicaci%C3%B3n-3.1%25-green) ![SEC](https://img.shields.io/badge/SEC-0-green) ![SQL](https://img.shields.io/badge/SQL-0-green) ![DBG](https://img.shields.io/badge/DBG-0-green) ![Capas](https://img.shields.io/badge/Capas-3-green) ![Tests](https://img.shields.io/badge/Tests-6-green) ![Cob](https://img.shields.io/badge/Cob-90.9%25-green) ![EP](https://img.shields.io/badge/EP-38-green)

**Calidad de servicios (heurístico):** índice **89/100** · cumple **14/15** · aprobado **SI** · capas **3**
Detalle completo en [`docs/EVALUACION.md`](docs/EVALUACION.md).
<!-- calidad:fin -->

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
