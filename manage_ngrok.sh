#!/bin/bash

# Script de gestion ngrok pour le dashboard climatique

case "$1" in
    start)
        echo "🚀 Démarrage de ngrok..."
        # Arrêter ngrok s'il est déjà en cours
        pkill -f "ngrok http 8501" 2>/dev/null || true
        sleep 2
        
        # Démarrer ngrok en arrière-plan
        nohup ngrok http 8501 > ngrok.out 2>&1 &
        sleep 3
        
        # Récupérer l'URL publique
        URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); tunnels=data['tunnels']; print(tunnels[0]['public_url'] if tunnels else '')" 2>/dev/null)
        
        if [ -n "$URL" ]; then
            echo "✅ ngrok démarré avec succès!"
            echo "🌐 URL publique: $URL?ngrok-skip-browser-warning=true"
            echo "📊 Dashboard local: http://localhost:8501"
            echo "🔧 Interface ngrok: http://localhost:4040"
        else
            echo "❌ Erreur lors du démarrage de ngrok"
            exit 1
        fi
        ;;
        
    stop)
        echo "🛑 Arrêt de ngrok..."
        pkill -f "ngrok http 8501"
        echo "✅ ngrok arrêté"
        ;;
        
    status)
        if pgrep -f "ngrok http 8501" > /dev/null; then
            echo "✅ ngrok est en cours d'exécution"
            URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); tunnels=data['tunnels']; print(tunnels[0]['public_url'] if tunnels else 'Non disponible')" 2>/dev/null)
            echo "🌐 URL publique: $URL?ngrok-skip-browser-warning=true"
        else
            echo "❌ ngrok n'est pas en cours d'exécution"
        fi
        ;;
        
    url)
        URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); tunnels=data['tunnels']; print(tunnels[0]['public_url'] if tunnels else '')" 2>/dev/null)
        if [ -n "$URL" ]; then
            echo "$URL?ngrok-skip-browser-warning=true"
        else
            echo "ngrok non actif"
            exit 1
        fi
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|url}"
        echo ""
        echo "Commandes:"
        echo "  start   - Démarre ngrok et expose le dashboard"
        echo "  stop    - Arrête ngrok"
        echo "  status  - Vérifie l'état de ngrok"
        echo "  url     - Affiche seulement l'URL publique"
        exit 1
        ;;
esac