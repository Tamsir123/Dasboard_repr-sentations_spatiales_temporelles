from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from services.data_processing import ClimateDataProcessor
from typing import Optional
import os
import sys
sys.path.append('..')

router = APIRouter()

# Instance globale du processeur de données
processor = ClimateDataProcessor()

@router.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    try:
        return {
            "status": "healthy",
            "message": "API Climate opérationnelle",
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/variables")
async def get_variables():
    """Retourne la liste des variables disponibles"""
    try:
        variables = processor.get_available_variables()
        time_range = processor.get_time_range()
        return {
            "variables": variables,
            "time_range": time_range
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/years")
async def get_available_years():
    """Retourne rapidement la liste de toutes les années disponibles"""
    try:
        years = processor.get_available_years()
        return {
            "years": years,
            "total": len(years),
            "start_year": min(years) if years else None,
            "end_year": max(years) if years else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/time-series")
async def get_time_series(
    var: str = Query(..., description="Variable (tasmin ou tasmax)"),
    start_year: int = Query(..., description="Année de début"),
    end_year: int = Query(..., description="Année de fin")
):
    """Retourne la série temporelle moyenne annuelle"""
    try:
        if var not in ["tasmin", "tasmax"]:
            raise HTTPException(status_code=400, detail="Variable doit être 'tasmin' ou 'tasmax'")
        
        if start_year > end_year:
            raise HTTPException(status_code=400, detail="L'année de début doit être <= année de fin")
        
        result = processor.get_time_series(var, start_year, end_year)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/climatology")
async def get_climatology(
    var: str = Query(..., description="Variable (tasmin ou tasmax)"),
    start_year: int = Query(..., description="Année de début"),
    end_year: int = Query(..., description="Année de fin")
):
    """Retourne la climatologie mensuelle moyenne"""
    try:
        if var not in ["tasmin", "tasmax"]:
            raise HTTPException(status_code=400, detail="Variable doit être 'tasmin' ou 'tasmax'")
        
        if start_year > end_year:
            raise HTTPException(status_code=400, detail="L'année de début doit être <= année de fin")
        
        result = processor.get_climatology(var, start_year, end_year)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spatial")
async def get_spatial_data(
    var: str = Query(..., description="Variable (tasmin ou tasmax)"),
    month: int = Query(..., description="Mois (1-12)", ge=1, le=12),
    start_year: int = Query(..., description="Année de début"),
    end_year: int = Query(..., description="Année de fin")
):
    """Retourne les données spatiales pour un mois donné"""
    try:
        if var not in ["tasmin", "tasmax"]:
            raise HTTPException(status_code=400, detail="Variable doit être 'tasmin' ou 'tasmax'")
        
        if start_year > end_year:
            raise HTTPException(status_code=400, detail="L'année de début doit être <= année de fin")
        
        result = processor.get_spatial_data(var, month, start_year, end_year)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_statistics(
    var: str = Query(..., description="Variable (tasmin ou tasmax)"),
    start_year: int = Query(..., description="Année de début"),
    end_year: int = Query(..., description="Année de fin")
):
    """Retourne les statistiques globales"""
    try:
        if var not in ["tasmin", "tasmax"]:
            raise HTTPException(status_code=400, detail="Variable doit être 'tasmin' ou 'tasmax'")
        
        if start_year > end_year:
            raise HTTPException(status_code=400, detail="L'année de début doit être <= année de fin")
        
        result = processor.get_statistics(var, start_year, end_year)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download")
async def download_data(
    var: str = Query(..., description="Variable (tasmin ou tasmax)"),
    start_year: int = Query(..., description="Année de début"),
    end_year: int = Query(..., description="Année de fin"),
    format_type: str = Query("csv", description="Format de téléchargement (csv ou netcdf)")
):
    """Télécharge les données dans le format demandé"""
    try:
        if var not in ["tasmin", "tasmax"]:
            raise HTTPException(status_code=400, detail="Variable doit être 'tasmin' ou 'tasmax'")
        
        if start_year > end_year:
            raise HTTPException(status_code=400, detail="L'année de début doit être <= année de fin")
        
        if format_type not in ["csv", "netcdf"]:
            raise HTTPException(status_code=400, detail="Format doit être 'csv' ou 'netcdf'")
        
        # Exporter les données
        filepath = processor.export_data(var, start_year, end_year, format_type)
        
        # Vérifier que le fichier existe
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Erreur lors de la génération du fichier")
        
        # Déterminer le type de média
        if format_type == "csv":
            media_type = "text/csv"
            filename = f"{var}_{start_year}_{end_year}.csv"
        else:  # netcdf
            media_type = "application/octet-stream"
            filename = f"{var}_{start_year}_{end_year}.nc"
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))