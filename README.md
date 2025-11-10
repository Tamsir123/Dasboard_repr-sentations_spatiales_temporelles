# 🌡️ Dashboard Climatique du Sénégal

Tableau de bord interactif pour la visualisation et l'analyse des données climatiques du Sénégal (1960-2024) avec FastAPI backend et Streamlit frontend.

![Dashboard Preview](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

## 📋 Structure du Projet

```
Dasboard/
├── backend/                 # API FastAPI
│   ├── main.py             # Point d'entrée de l'API
│   ├── routers/
│   │   └── climate.py      # Routes climatiques
│   ├── services/
│   │   └── data_processing.py  # Traitement des données
│   ├── data/               # Fichiers NetCDF
│   │   ├── tasmin_daily_Senegal_1960_2024.nc
│   │   └── tasmax_daily_Senegal_1960_2024.nc
│   └── requirements.txt
├── frontend/               # Interface Streamlit
│   ├── dashboard.py        # Application principale
│   └── requirements.txt
└── README.md
```

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.8+
- pip

### Installation Locale

**1. Installer les dépendances Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**2. Installer les dépendances Frontend:**
```bash
cd frontend
pip install -r requirements.txt
```

**3. Démarrer l'API (Terminal 1):**
```bash
cd backend
python main.py
```
→ API disponible sur http://localhost:8000

**4. Démarrer l'Interface (Terminal 2):**
```bash
cd frontend
streamlit run dashboard.py
```
→ Dashboard disponible sur http://localhost:8501

## 🌐 Déploiement Streamlit Cloud

### Étapes pour déployer gratuitement :

1. **Pousser sur GitHub** (déjà fait ✅)
2. **Aller sur** [streamlit.io/cloud](https://streamlit.io/cloud)
3. **Connecter votre compte GitHub**
4. **Créer une nouvelle app :**
   - Repository : `Dasboard_repr-sentations_spatiales_temporelles`
   - Main file path : `frontend/dashboard.py`
   - Python version : 3.9
5. **Cliquer "Deploy!"**

Votre app sera accessible sur : `https://votre-app.streamlit.app`

## 🌟 Fonctionnalités

### 📈 Série Temporelle
- Évolution annuelle des températures (1960-2024)
- Calcul automatique des statistiques
- Graphiques interactifs avec Plotly

### 📅 Climatologie Mensuelle
- Cycle saisonnier moyen sur la période sélectionnée
- Identification des mois les plus chauds/froids
- Visualisation en barres colorées

### 🗺️ Cartes Spatiales
- Distribution spatiale mensuelle des températures
- Cartes interactives avec échelle de couleur
- Sélection du mois d'intérêt

### 📊 Statistiques Détaillées
- Statistiques globales sur la période sélectionnée
- Métriques de dispersion et extremes
- Interface claire avec cartes colorées

### ⬇️ Téléchargement de Données
- Export des données filtrées en CSV ou NetCDF
- Paramètres personnalisables (variable, période)
- Téléchargement direct depuis l'interface

## 🔧 API Endpoints

### Variables et Métadonnées
- `GET /api/v1/climate/variables` - Variables disponibles
- `GET /api/v1/climate/years` - Années disponibles
- `GET /api/v1/climate/health` - État de l'API

### Données Climatiques
- `GET /api/v1/climate/time-series` - Série temporelle
- `GET /api/v1/climate/climatology` - Climatologie mensuelle
- `GET /api/v1/climate/spatial` - Données spatiales
- `GET /api/v1/climate/stats` - Statistiques globales
- `GET /api/v1/climate/download` - Téléchargement de fichiers

### Documentation Interactive
Une fois l'API démarrée : http://localhost:8000/docs

## 🗺️ Couverture Géographique

**Région :** Sénégal, Afrique de l'Ouest
- **Latitudes :** 12°N à 17°N
- **Longitudes :** -18°W à -11°W
- **Résolution :** Grille spatiale haute résolution
- **Période :** 64 ans de données (1960-2024)
- **Variables :** Températures minimales et maximales journalières

## 🛠️ Technologies Utilisées

**Backend:**
- FastAPI (API REST moderne)
- Xarray (Manipulation NetCDF)
- NumPy & Pandas (Calculs scientifiques)
- Uvicorn (Serveur ASGI)

**Frontend:**
- Streamlit (Interface web interactive)
- Plotly (Graphiques interactifs)
- Requests (Communication API)

## 🐛 Dépannage

### L'API ne démarre pas
- Vérifiez que les fichiers NetCDF sont dans `backend/data/`
- Assurez-vous que toutes les dépendances sont installées
- Vérifiez que le port 8000 est libre

### L'interface affiche une erreur de connexion
- Vérifiez que l'API est démarrée sur http://localhost:8000
- Testez l'API directement : http://localhost:8000/docs
- Vérifiez l'URL de l'API dans le code frontend

### Problèmes avec les données NetCDF
- Vérifiez les noms des variables dans vos fichiers NetCDF
- Adaptez les noms dans `data_processing.py` si nécessaire
- Consultez les logs de l'API pour plus de détails

## 🤝 Contribution

Ce projet est open-source. N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Contribuer au code
- Améliorer la documentation

## 📄 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.

---

**Développé pour l'analyse climatique du Sénégal 🇸🇳**

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)