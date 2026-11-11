FROM python:3.12-slim

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY app ./app

# Exponer puerto
EXPOSE 5001

# Comando de entrada
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]