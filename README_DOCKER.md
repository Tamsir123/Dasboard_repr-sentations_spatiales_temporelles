# 🐳 Dockerisation Dashboard Climatique Sénégal

## Structure finale
```
Dasboard/
├── backend/                    # API FastAPI
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── routers/
│   ├── services/
│   └── data/
├── frontend/                   # Dashboard Streamlit
│   ├── dashboard.py
│   ├── config.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml          # Orchestration
├── .env                       # Variables d'environnement
├── nginx/                     # Reverse proxy (bonus)
│   ├── nginx.conf
│   └── Dockerfile
└── README_DOCKER.md
```

## 🎯 Objectifs atteints
✅ Backend FastAPI sur port 8000
✅ Frontend Streamlit sur port 8501
✅ Communication interne via réseau Docker
✅ Exposition publique via ngrok ou VPS
✅ Reverse proxy Nginx (bonus)
✅ Variables d'environnement configurables