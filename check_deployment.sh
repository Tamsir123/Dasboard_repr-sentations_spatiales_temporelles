#!/bin/bash

# Script de vérification post-déploiement
echo "🔍 Vérification du déploiement Docker"
echo "====================================="

# Vérifier les conteneurs
echo "📦 Conteneurs actifs:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔗 Tests de connectivité:"

# Test Backend
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API: http://localhost:8000 (OK)"
else
    echo "❌ Backend API: http://localhost:8000 (FAIL)"
fi

# Test Frontend
if curl -f -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Frontend Dashboard: http://localhost:8501 (OK)"
else
    echo "⚠️  Frontend Dashboard: http://localhost:8501 (En cours de démarrage...)"
fi

echo ""
echo "📚 URLs importantes:"
echo "   Dashboard: http://localhost:8501"
echo "   API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   API Health: http://localhost:8000/health"

echo ""
echo "🔧 Commandes utiles:"
echo "   docker ps                    # Voir les conteneurs"
echo "   docker logs climate_api      # Logs backend"
echo "   docker logs climate_dashboard # Logs frontend"
echo "   ./deploy_docker.sh stop      # Arrêter les services"