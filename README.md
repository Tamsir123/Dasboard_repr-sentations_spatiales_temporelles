# 🌍 Dashboard Climatique Sénégal

Dashboard interactif pour visualiser et analyser les données climatiques du Sénégal (1960-2024).

## 🏗️ Architecture

```
📦 Dasboard/
├── 🐳 docker-compose.yml          # Configuration Docker
├── ⚙️ .env                        # Variables d'environnement
├── 📝 README.md                   # Documentation
├── 🌐 manage_ngrok.sh             # Gestion tunnel ngrok
├── 📄 url_publique.txt            # URLs d'accès
│
├── 🖥️ frontend/                   # Interface Streamlit
│   ├── 📊 dashboard.py            # Application principale
│   ├── ⚙️ config.py               # Configuration frontend
│   ├── 🐳 Dockerfile              # Image Docker frontend
│   ├── 📦 requirements.txt        # Dépendances Python
│   ├── 🖼️ logo_climasene.png      # Logo application
│   └── .streamlit/
│       └── config.toml             # Configuration Streamlit
│
└── 🔌 backend dasboard climatique/ # API FastAPI
    ├── 🚀 main.py                 # Serveur API principal
    ├── 🐳 Dockerfile              # Image Docker backend
    ├── 📦 requirements.txt        # Dépendances Python
    │
    ├── 🛣️ routers/                # Routes API
    │   └── climate.py             # Endpoints climatiques
    │
    ├── ⚙️ services/               # Logique métier
    │   └── csv_data_processing.py # Traitement données
    │
    └── 📊 data/                   # Données climatiques
        ├── senegal_cities.csv     # 15 villes principales
        ├── senegal_grid_points.csv # 609 points de grille
        └── csv_optimized/         # Données NetCDF optimisées
            ├── tasmax_daily_Senegal_1960_2024_optimized.csv
            └── tasmin_daily_Senegal_1960_2024_optimized.csv
```

## 🚀 Démarrage rapide

### 1. Lancer les services Docker
```bash
docker-compose up -d
```

### 2. Accès local
- **Dashboard** : http://localhost:8501
- **API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs

### 3. Accès public (ngrok)
```bash
./manage_ngrok.sh start    # Démarrer ngrok
./manage_ngrok.sh url      # Obtenir l'URL publique
./manage_ngrok.sh status   # Vérifier l'état
./manage_ngrok.sh stop     # Arrêter ngrok
```

## 📊 Fonctionnalités

### ✅ Données disponibles
- **Variables** : Température minimale (tasmin), Température maximale (tasmax)
- **Période** : 1960-2024 (64 ans)
- **Localités** : 15 villes principales du Sénégal
- **Résolution** : Données quotidiennes

### ✅ Visualisations
- 📈 Séries temporelles interactives
- 🗺️ Cartes climatiques
- 📊 Analyses statistiques
- 📥 Export direct des données (CSV/NetCDF)

### ✅ Interface utilisateur
- 🎯 Sélection intuitive des paramètres
- ⚡ Téléchargement en un clic
- 📱 Interface responsive
- 🌐 Accès public via ngrok

## 🏛️ Localités disponibles

1. **Dakar** - Capitale (14.72°N, -17.47°W)
2. **Thiès** - Région de Thiès (14.79°N, -16.93°W)
3. **Kaolack** - Région de Kaolack (14.16°N, -16.07°W)
4. **Saint-Louis** - Ancienne capitale (16.05°N, -16.48°W)
5. **Ziguinchor** - Casamance (12.57°N, -16.27°W)
6. **Diourbel** - Bassin arachidier (14.66°N, -16.24°W)
7. **Tambacounda** - Est du pays (13.77°N, -13.67°W)
8. **Kolda** - Sud-est (12.89°N, -14.94°W)
9. **Fatick** - Centre (14.33°N, -16.41°W)
10. **Louga** - Nord (15.62°N, -16.25°W)
11. **Matam** - Fleuve Sénégal (15.66°N, -13.26°W)
12. **Kaffrine** - Centre-est (14.11°N, -15.55°W)
13. **Kédougou** - Sud-est montagneux (12.56°N, -12.18°W)
14. **Sédhiou** - Sud (12.71°N, -15.56°W)
15. **Mbour** - Petite Côte (14.42°N, -16.96°W)

## 🔧 Configuration

### Variables d'environnement (.env)
```env
# Mode de déploiement
DEPLOYMENT_MODE=docker

# URLs API
API_BASE_URL=http://backend:8000/api/v1/climate
API_BASE_URL_LOCAL=http://localhost:8000/api/v1/climate

# Configuration Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Debug
DEBUG_MODE=false
```

### Ports utilisés
- **8501** : Frontend Streamlit
- **8000** : Backend FastAPI
- **4040** : Interface ngrok (local)

## 🛠️ Maintenance

### Rebuilder les conteneurs
```bash
docker-compose build
docker-compose up -d
```

### Voir les logs
```bash
docker-compose logs frontend
docker-compose logs backend
```

### Nettoyer Docker
```bash
docker-compose down
docker system prune -f
```

## 📚 API Endpoints

### Localités
- `GET /api/v1/climate/localities` - Toutes les localités
- `GET /api/v1/climate/localities/cities` - Villes uniquement

### Données climatiques
- `GET /api/v1/climate/time-series` - Séries temporelles
- `GET /api/v1/climate/climatology` - Climatologie
- `GET /api/v1/climate/spatial` - Données spatiales
- `GET /api/v1/climate/download` - Export données

### Utilitaires
- `GET /api/v1/climate/health` - Santé API
- `GET /api/v1/climate/variables` - Variables disponibles
- `GET /docs` - Documentation interactive

## 🔗 Liens utiles

- **Dashboard public** : Voir `url_publique.txt`
- **Dépôt GitHub** : kaolack_Services (branche: feature/improved-front)
- **Documentation Streamlit** : https://docs.streamlit.io
- **Documentation FastAPI** : https://fastapi.tiangolo.com

## 👥 Équipe

Dashboard développé pour l'analyse climatique au Sénégal.

---

*Dernière mise à jour : Novembre 2025*