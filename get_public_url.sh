#!/bin/bash

# Script pour obtenir et mettre à jour l'URL ngrok

# Récupérer l'URL publique actuelle
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null)

if [ "$NGROK_URL" != "null" ] && [ -n "$NGROK_URL" ]; then
    echo "🌍 URL publique ngrok: $NGROK_URL"
    
    # Mettre à jour le fichier .env
    if [ -f ".env" ]; then
        sed -i "s|NGROK_URL=.*|NGROK_URL=$NGROK_URL|" .env
        echo "✅ URL mise à jour dans .env"
    fi
    
    echo ""
    echo "📋 Partagez cette URL:"
    echo "   $NGROK_URL"
else
    echo "❌ Ngrok n'est pas actif ou aucun tunnel trouvé"
    echo "💡 Démarrer ngrok: ngrok http 8501"
fi