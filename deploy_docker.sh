#!/bin/bash

# Script de déploiement Docker pour Dashboard Climatique
# Usage: ./deploy_docker.sh [mode]
# Modes: simple, nginx, dev

set -e

MODE=${1:-simple}

echo "🐳 Déploiement Docker - Dashboard Climatique Sénégal"
echo "=================================================="
echo "Mode: $MODE"
echo ""

# Détection de la commande Docker Compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose non trouvé. Veuillez l'installer."
    exit 1
fi

echo "🔧 Utilisation de: $DOCKER_COMPOSE"
echo ""

# Fonction de nettoyage
cleanup() {
    echo "🧹 Nettoyage des conteneurs existants..."
    $DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true
    $DOCKER_COMPOSE -f docker-compose.nginx.yml down --remove-orphans 2>/dev/null || true
}

# Fonction de build
build_and_run() {
    local compose_file=$1
    echo "🔧 Build et démarrage des conteneurs..."
    $DOCKER_COMPOSE -f $compose_file up --build -d
    
    echo "⏳ Attente du démarrage des services..."
    sleep 15
    
    echo "📊 Statut des conteneurs:"
    $DOCKER_COMPOSE -f $compose_file ps
}

# Tests de connectivité
test_services() {
    local frontend_url=$1
    local backend_url=$2
    
    echo ""
    echo "🧪 Tests de connectivité..."
    
    # Test backend
    if curl -f -s "$backend_url/health" > /dev/null; then
        echo "✅ Backend accessible: $backend_url"
    else
        echo "❌ Backend inaccessible: $backend_url"
    fi
    
    # Test frontend (plus complexe pour Streamlit)
    if curl -f -s "$frontend_url" > /dev/null; then
        echo "✅ Frontend accessible: $frontend_url"
    else
        echo "⚠️  Frontend en cours de démarrage: $frontend_url"
    fi
}

case $MODE in
    "simple")
        echo "🚀 Déploiement simple (backend + frontend)"
        cleanup
        build_and_run "docker-compose.yml"
        test_services "http://localhost:8501" "http://localhost:8000"
        echo ""
        echo "🎉 Déploiement terminé !"
        echo "📊 Dashboard: http://localhost:8501"
        echo "🔌 API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
        ;;
        
    "nginx")
        echo "🚀 Déploiement avec Nginx (reverse proxy)"
        cleanup
        build_and_run "docker-compose.nginx.yml"
        test_services "http://localhost" "http://localhost/api"
        echo ""
        echo "🎉 Déploiement terminé !"
        echo "🌐 Application: http://localhost (port 80)"
        echo "🌐 Alternative: http://localhost:8080"
        echo "📊 Dashboard: http://localhost"
        echo "🔌 API: http://localhost/api"
        ;;
        
    "dev")
        echo "🚀 Déploiement développement (avec logs)"
        cleanup
        echo "🔧 Build des images..."
        $DOCKER_COMPOSE build
        echo "🔄 Démarrage en mode développement (logs visibles)..."
        $DOCKER_COMPOSE up
        ;;
        
    "stop")
        echo "🛑 Arrêt des services..."
        cleanup
        echo "✅ Services arrêtés"
        ;;
        
    *)
        echo "❌ Mode inconnu: $MODE"
        echo "Modes disponibles: simple, nginx, dev, stop"
        exit 1
        ;;
esac