#!/bin/bash
# Script de despliegue para Ticketera Admin API
# Uso: ./deploy.sh [up|down|build|logs|restart]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "${1:-up}" in
  up)
    echo "🚀 Iniciando Ticketera Admin API con Docker..."
    cd "$PROJECT_DIR"
    docker compose up -d --build
    echo ""
    echo "✅ Servicios iniciados"
    echo "   - API FastAPI: http://localhost:5001"
    echo "   - MySQL: localhost:3306"
    echo "   - Health check: http://localhost:5001/api/health"
    ;;
  
  down)
    echo "🛑 Deteniendo Ticketera Admin API..."
    cd "$PROJECT_DIR"
    docker compose down
    echo ""
    echo "✅ Servicios detenidos"
    ;;
    
  build)
    echo "🔨 Construyendo imágenes..."
    cd "$PROJECT_DIR"
    docker compose build
    echo ""
    echo "✅ Imágenes construidas"
    ;;
    
  logs)
    echo "📋 Ver logs..."
    cd "$PROJECT_DIR"
    docker compose logs -f "${2:-app}"
    ;;
    
  restart)
    echo "🔄 Reiniciando servicios..."
    cd "$PROJECT_DIR"
    docker compose restart
    echo ""
    echo "✅ Servicios reiniciados"
    ;;
    
  *)
    echo "Uso: $0 [up|down|build|logs|restart]"
    echo ""
    echo "Comandos disponibles:"
    echo "  up      - Iniciar todos los servicios"
    echo "  down    - Detener todos los servicios"
    echo "  build   - Construir imágenes Docker"
    echo "  logs    - Ver logs (opcional: servicio específico)"
    echo "  restart - Reiniciar servicios"
    exit 1
    ;;
esac