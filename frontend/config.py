"""
Configuration pour le dashboard climatique
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de l'API - Priorité aux variables d'environnement Docker
API_BASE_URL = os.getenv('API_BASE_URL', 'http://backend:8000/api/v1/climate')
API_BASE_URL_LOCAL = os.getenv('API_BASE_URL_LOCAL', 'http://localhost:8000/api/v1/climate')
API_BASE_URL_REMOTE = os.getenv('API_BASE_URL_REMOTE', 'https://backend-dasboard-climatique-1.onrender.com/api/v1/climate')

# Configuration Streamlit
STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', 8501))
STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')

# Mode de déploiement
DEPLOYMENT_MODE = os.getenv('DEPLOYMENT_MODE', 'docker').lower()  # docker, local, remote
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

def get_api_url():
    """Retourne l'URL de l'API selon le mode de déploiement"""
    if DEPLOYMENT_MODE == 'docker':
        return API_BASE_URL  # http://backend:8000/api/v1/climate
    elif DEPLOYMENT_MODE == 'local':
        return API_BASE_URL_LOCAL  # http://localhost:8000/api/v1/climate
    elif DEPLOYMENT_MODE == 'remote':
        return API_BASE_URL_REMOTE  # URL Render/Railway
    else:
        return API_BASE_URL  # Par défaut Docker

# Affichage de la configuration (pour debug)
if DEBUG_MODE:
    print(f"🔧 Configuration:")
    print(f"   API URL: {get_api_url()}")
    print(f"   Streamlit Port: {STREAMLIT_SERVER_PORT}")
    print(f"   Debug Mode: {DEBUG_MODE}")