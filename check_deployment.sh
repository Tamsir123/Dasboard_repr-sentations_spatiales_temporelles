#!/bin/bash

# Vérification des services
echo "🔍 Vérification des services Docker"

# Statut des conteneurs
echo "📦 Conteneurs:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🔗 Connectivité:"

# Tests
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API: http://localhost:8000"
else
    echo "❌ API indisponible"
fi

if curl -f -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Dashboard: http://localhost:8501"
else
    echo "❌ Dashboard indisponible"
fi