from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import climate
import uvicorn

# Création de l'application FastAPI
app = FastAPI(
    title="API Données Climatiques Sénégal",
    description="API pour l'analyse et la visualisation des données climatiques du Sénégal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(climate.router, prefix="/api/v1/climate", tags=["climate"])

# Point de terminaison racine
@app.get("/")
async def root():
    return {
        "message": "API Données Climatiques Sénégal",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/climate/health"
    }

# Point de santé global
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "climate-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)