# import xarray as xr
# import pandas as pd
# import numpy as np
# from typing import Dict, List, Optional, Tuple
# import os
# from pathlib import Path
# from functools import lru_cache
# import pickle
# import time

# class ClimateDataProcessor:
#     def __init__(self, data_dir: str = "data"):
#         # S'assurer d'utiliser le chemin relatif au script
#         script_dir = Path(__file__).parent.parent  # Remonter au dossier backend
#         self.data_dir = script_dir / data_dir
#         self.tasmin_path = self.data_dir / "tasmin_daily_Senegal_1960_2024.nc"
#         self.tasmax_path = self.data_dir / "tasmax_daily_Senegal_1960_2024.nc"
        
#         # Fichiers de localités
#         self.cities_file = self.data_dir / "senegal_cities.csv"
#         self.grid_points_file = self.data_dir / "senegal_grid_points.csv"
        
#         print(f"Répertoire des données: {self.data_dir}")
#         print(f"Chemin tasmin: {self.tasmin_path}")
#         print(f"Chemin tasmax: {self.tasmax_path}")
        
#         # Cache pour éviter de recharger les données
#         self._tasmin_ds = None
#         self._tasmax_ds = None
#         self._tasmin = None
#         self._tasmax = None
        
#         # Cache pour les localités
#         self._cities_data = None
#         self._grid_points_data = None
        
#         # Cache agressif pour les résultats calculés
#         self._result_cache = {}
#         self._cache_expiry = 3600  # 1 heure
    
#     def _get_cache_key(self, method: str, *args) -> str:
#         """Génère une clé de cache unique"""
#         return f"{method}_{hash(str(args))}"
    
#     def _get_cached_result(self, cache_key: str):
#         """Récupère un résultat du cache s'il est valide"""
#         if cache_key in self._result_cache:
#             result, timestamp = self._result_cache[cache_key]
#             if time.time() - timestamp < self._cache_expiry:
#                 return result
#             else:
#                 # Cache expiré, le supprimer
#                 del self._result_cache[cache_key]
#         return None
    
#     def _set_cached_result(self, cache_key: str, result):
#         """Met en cache un résultat"""
#         self._result_cache[cache_key] = (result, time.time())
    
#     def _load_data(self):
#         """Charge les données NetCDF si pas déjà en cache - OPTIMISÉ"""
#         if self._tasmin_ds is None:
#             if self.tasmin_path.exists():
#                 print("Chargement tasmin... (peut prendre quelques secondes)")
#                 # Chargement simple sans chunks pour éviter les problèmes Dask
#                 self._tasmin_ds = xr.open_dataset(self.tasmin_path)
#                 self._tasmin = self._tasmin_ds['tasmin']
#                 print("✅ Tasmin chargé")
#             else:
#                 raise FileNotFoundError(f"Fichier tasmin non trouvé: {self.tasmin_path}")
        
#         if self._tasmax_ds is None:
#             if self.tasmax_path.exists():
#                 print("Chargement tasmax... (peut prendre quelques secondes)")
#                 # Chargement simple sans chunks pour éviter les problèmes Dask
#                 self._tasmax_ds = xr.open_dataset(self.tasmax_path)
#                 self._tasmax = self._tasmax_ds['tasmax']
#                 print("✅ Tasmax chargé")
#             else:
#                 raise FileNotFoundError(f"Fichier tasmax non trouvé: {self.tasmax_path}")
    
#     def get_available_variables(self) -> List[str]:
#         """Retourne la liste des variables disponibles"""
#         return ["tasmin", "tasmax"]
    
#     def get_time_range(self) -> Dict[str, int]:
#         """Retourne la plage temporelle disponible"""
#         self._load_data()
#         time_coords = self._tasmin.time
#         start_year = int(time_coords.dt.year.min().values)
#         end_year = int(time_coords.dt.year.max().values)
#         return {"start_year": start_year, "end_year": end_year}
    
#     @lru_cache(maxsize=1)
#     def get_available_years(self) -> List[int]:
#         """Retourne rapidement la liste de toutes les années disponibles - CACHE PERMANENT"""
#         self._load_data()
#         # Utiliser tasmin comme référence pour les années (plus rapide)
#         years = pd.to_datetime(self._tasmin.time.values).year
#         unique_years = sorted(set(years))
#         return unique_years
    
#     def get_time_series(self, variable: str, start_year: int, end_year: int) -> Dict:
#         """Calcule la série temporelle moyenne annuelle - CACHE OPTIMISÉ"""
#         cache_key = self._get_cache_key("time_series", variable, start_year, end_year)
        
#         # Vérifier le cache d'abord
#         cached_result = self._get_cached_result(cache_key)
#         if cached_result is not None:
#             return cached_result
        
#         self._load_data()
        
#         # Sélectionner la variable
#         if variable == "tasmin":
#             data = self._tasmin
#         elif variable == "tasmax":
#             data = self._tasmax
#         else:
#             raise ValueError(f"Variable inconnue: {variable}")
        
#         # Filtrer par période - optimisation : utiliser isel si possible
#         data_filtered = data.sel(time=slice(f"{start_year}", f"{end_year}"))
        
#         # Calculer la moyenne annuelle spatiale - optimisé
#         annual_mean = data_filtered.resample(time="1Y").mean().mean(dim=['latitude', 'longitude'])
        
#         # Convertir en format JSON-friendly
#         years = annual_mean.time.dt.year.values.tolist()
#         values = [float(v) for v in annual_mean.values]  # Conversion explicite
        
#         result = {
#             "variable": variable,
#             "start_year": start_year,
#             "end_year": end_year,
#             "years": years,
#             "values": values,
#             "unit": "°C"
#         }
        
#         # Mettre en cache
#         self._set_cached_result(cache_key, result)
#         return result
    
#     def get_climatology(self, variable: str, start_year: int, end_year: int) -> Dict:
#         """Calcule la climatologie mensuelle moyenne - CACHE OPTIMISÉ"""
#         cache_key = self._get_cache_key("climatology", variable, start_year, end_year)
        
#         # Vérifier le cache d'abord
#         cached_result = self._get_cached_result(cache_key)
#         if cached_result is not None:
#             return cached_result
        
#         self._load_data()
        
#         # Sélectionner la variable
#         if variable == "tasmin":
#             data = self._tasmin
#         elif variable == "tasmax":
#             data = self._tasmax
#         else:
#             raise ValueError(f"Variable inconnue: {variable}")
        
#         # Filtrer par période
#         data_filtered = data.sel(time=slice(f"{start_year}", f"{end_year}"))
        
#         # Calculer la climatologie mensuelle - optimisé
#         data_monthly = data_filtered.groupby('time.month').mean(dim='time')
        
#         # Moyenne spatiale
#         monthly_mean = data_monthly.mean(dim=['latitude', 'longitude'])
        
#         months = monthly_mean.month.values.tolist()
#         values = [float(v) for v in monthly_mean.values]  # Conversion explicite
        
#         result = {
#             "variable": variable,
#             "start_year": start_year,
#             "end_year": end_year,
#             "months": months,
#             "values": values,
#             "unit": "°C"
#         }
        
#         # Mettre en cache
#         self._set_cached_result(cache_key, result)
#         return result
    
#     def get_spatial_data(self, variable: str, month: int, start_year: int, end_year: int) -> Dict:
#         """Retourne les données spatiales pour un mois donné - CACHE OPTIMISÉ"""
#         cache_key = self._get_cache_key("spatial", variable, month, start_year, end_year)
        
#         # Vérifier le cache d'abord
#         cached_result = self._get_cached_result(cache_key)
#         if cached_result is not None:
#             return cached_result
        
#         self._load_data()
        
#         # Sélectionner la variable
#         if variable == "tasmin":
#             data = self._tasmin
#         elif variable == "tasmax":
#             data = self._tasmax
#         else:
#             raise ValueError(f"Variable inconnue: {variable}")
        
#         # Filtrer par période
#         data_filtered = data.sel(time=slice(f"{start_year}", f"{end_year}"))
        
#         # Calculer la climatologie mensuelle - optimisé
#         data_monthly = data_filtered.groupby('time.month').mean(dim='time')
        
#         # Sélectionner le mois
#         monthly_data = data_monthly.sel(month=month)
        
#         result = {
#             "variable": variable,
#             "month": month,
#             "start_year": start_year,
#             "end_year": end_year,
#             "latitudes": monthly_data.latitude.values.tolist(),
#             "longitudes": monthly_data.longitude.values.tolist(),
#             "values": monthly_data.values.tolist(),
#             "unit": "°C"
#         }
        
#         # Mettre en cache
#         self._set_cached_result(cache_key, result)
#         return result
    
#     def get_statistics(self, variable: str, start_year: int, end_year: int) -> Dict:
#         """Calcule les statistiques globales - CACHE OPTIMISÉ"""
#         cache_key = self._get_cache_key("statistics", variable, start_year, end_year)
        
#         # Vérifier le cache d'abord
#         cached_result = self._get_cached_result(cache_key)
#         if cached_result is not None:
#             return cached_result
        
#         self._load_data()
        
#         # Sélectionner la variable
#         if variable == "tasmin":
#             data = self._tasmin
#         elif variable == "tasmax":
#             data = self._tasmax
#         else:
#             raise ValueError(f"Variable inconnue: {variable}")
        
#         # Filtrer par période
#         data_filtered = data.sel(time=slice(f"{start_year}", f"{end_year}"))
        
#         # Calculer les statistiques de façon optimisée
#         result = {
#             "variable": variable,
#             "start_year": start_year,
#             "end_year": end_year,
#             "mean": float(data_filtered.mean().values),
#             "min": float(data_filtered.min().values),
#             "max": float(data_filtered.max().values),
#             "std": float(data_filtered.std().values),
#             "unit": "°C"
#         }
        
#         # Mettre en cache
#         self._set_cached_result(cache_key, result)
#         return result
    
#     def export_data(self, variable: str, start_year: int, end_year: int, format_type: str = "csv") -> str:
#         """Exporte les données dans le format demandé"""
#         self._load_data()
        
#         # Sélectionner la variable
#         if variable == "tasmin":
#             data = self._tasmin
#         elif variable == "tasmax":
#             data = self._tasmax
#         else:
#             raise ValueError(f"Variable inconnue: {variable}")
        
#         # Filtrer par période
#         data_filtered = data.sel(time=slice(f"{start_year}", f"{end_year}"))
        
#         if format_type == "csv":
#             # Convertir en DataFrame et sauvegarder en CSV
#             df = data_filtered.to_dataframe().reset_index()
#             filename = f"{variable}_{start_year}_{end_year}.csv"
#             filepath = self.data_dir / filename
#             df.to_csv(filepath, index=False)
#             return str(filepath)
        
#         elif format_type == "netcdf":
#             # Sauvegarder en NetCDF
#             filename = f"{variable}_{start_year}_{end_year}.nc"
#             filepath = self.data_dir / filename
#             data_filtered.to_netcdf(filepath)
#             return str(filepath)
        
#         else:
#             raise ValueError(f"Format non supporté: {format_type}")
    
#     def get_available_localities(self) -> Dict:
#         """Retourne toutes les localités disponibles (villes + points de grille)"""
#         cities = self.get_cities()
#         grid_points = self.get_grid_points()
        
#         return {
#             "cities": cities,
#             "grid_points": grid_points[:50],  # Limiter à 50 pour l'interface
#             "total_grid_points": len(grid_points),
#             "summary": {
#                 "cities_count": len(cities),
#                 "grid_points_count": len(grid_points),
#                 "coverage": {
#                     "lat_range": [12.0, 17.0],
#                     "lon_range": [-18.0, -11.0]
#                 }
#             }
#         }
    
#     def get_cities(self) -> List[Dict]:
#         """Charge et retourne les villes principales du Sénégal"""
#         if self._cities_data is None:
#             if self.cities_file.exists():
#                 df = pd.read_csv(self.cities_file)
#                 self._cities_data = df.to_dict('records')
#             else:
#                 self._cities_data = []
#         return self._cities_data
    
#     def get_grid_points(self) -> List[Dict]:
#         """Charge et retourne tous les points de grille"""
#         if self._grid_points_data is None:
#             if self.grid_points_file.exists():
#                 df = pd.read_csv(self.grid_points_file)
#                 self._grid_points_data = df.to_dict('records')
#             else:
#                 self._grid_points_data = []
#         return self._grid_points_data
    
#     def get_locality_time_series(self, variable: str, lat_idx: int, lon_idx: int, 
#                                 start_year: int, end_year: int) -> Dict:
#         """Récupère la série temporelle pour une localité spécifique"""
#         cache_key = self._get_cache_key("locality_time_series", variable, lat_idx, lon_idx, start_year, end_year)
        
#         # Vérifier le cache
#         cached_result = self._get_cached_result(cache_key)
#         if cached_result is not None:
#             return cached_result
        
#         self._load_data()
        
#         # Sélectionner la variable
#         if variable == "tasmin":
#             data = self._tasmin
#         elif variable == "tasmax":
#             data = self._tasmax
#         else:
#             raise ValueError(f"Variable inconnue: {variable}")
        
#         # Sélectionner le point spécifique
#         point_data = data.isel(latitude=lat_idx, longitude=lon_idx)
        
#         # Filtrer par période
#         data_filtered = point_data.sel(time=slice(f"{start_year}", f"{end_year}"))
        
#         # Calculer la moyenne annuelle
#         annual_mean = data_filtered.resample(time="1Y").mean()
        
#         # Convertir en format JSON-friendly
#         years = annual_mean.time.dt.year.values.tolist()
#         values = [float(v) if not np.isnan(v) else None for v in annual_mean.values]
        
#         result = {
#             "variable": variable,
#             "lat_idx": lat_idx,
#             "lon_idx": lon_idx,
#             "latitude": float(data.latitude.values[lat_idx]),
#             "longitude": float(data.longitude.values[lon_idx] - 360 if data.longitude.values[lon_idx] > 180 else data.longitude.values[lon_idx]),
#             "start_year": start_year,
#             "end_year": end_year,
#             "years": years,
#             "values": values,
#             "unit": "°C"
#         }
        
#         # Mettre en cache
#         self._set_cached_result(cache_key, result)
#         return result
    
#     def get_locality_statistics(self, variable: str, lat_idx: int, lon_idx: int,
#                                start_year: int, end_year: int) -> Dict:
#         """Calcule les statistiques pour une localité spécifique"""
#         cache_key = self._get_cache_key("locality_stats", variable, lat_idx, lon_idx, start_year, end_year)
        
#         # Vérifier le cache
#         cached_result = self._get_cached_result(cache_key)
#         if cached_result is not None:
#             return cached_result
        
#         self._load_data()
        
#         # Sélectionner la variable
#         if variable == "tasmin":
#             data = self._tasmin
#         elif variable == "tasmax":
#             data = self._tasmax
#         else:
#             raise ValueError(f"Variable inconnue: {variable}")
        
#         # Sélectionner le point spécifique
#         point_data = data.isel(latitude=lat_idx, longitude=lon_idx)
        
#         # Filtrer par période
#         data_filtered = point_data.sel(time=slice(f"{start_year}", f"{end_year}"))
        
#         # Calculer les statistiques
#         result = {
#             "variable": variable,
#             "lat_idx": lat_idx,
#             "lon_idx": lon_idx,
#             "latitude": float(data.latitude.values[lat_idx]),
#             "longitude": float(data.longitude.values[lon_idx] - 360 if data.longitude.values[lon_idx] > 180 else data.longitude.values[lon_idx]),
#             "start_year": start_year,
#             "end_year": end_year,
#             "mean": float(data_filtered.mean().values),
#             "min": float(data_filtered.min().values),
#             "max": float(data_filtered.max().values),
#             "std": float(data_filtered.std().values),
#             "unit": "°C"
#         }
        
#         # Mettre en cache
#         self._set_cached_result(cache_key, result)
#         return result
    
#     def find_locality_by_coordinates(self, lat: float, lon: float, tolerance: float = 0.5) -> Dict:
#         """Trouve la localité la plus proche des coordonnées données"""
#         self._load_data()
        
#         latitudes = self._tasmin.latitude.values
#         longitudes = self._tasmin.longitude.values
        
#         # Convertir les longitudes
#         longitudes_converted = np.where(longitudes > 180, longitudes - 360, longitudes)
        
#         # Trouver le point le plus proche
#         lat_diff = np.abs(latitudes - lat)
#         lon_diff = np.abs(longitudes_converted - lon)
        
#         lat_idx = np.argmin(lat_diff)
#         lon_idx = np.argmin(lon_diff)
        
#         grid_lat = latitudes[lat_idx]
#         grid_lon = longitudes_converted[lon_idx]
        
#         # Calculer la distance
#         distance = np.sqrt((lat - grid_lat)**2 + (lon - grid_lon)**2) * 111  # Approximation en km
        
#         if distance > tolerance * 111:  # Si trop loin
#             return None
        
#         return {
#             "lat_idx": int(lat_idx),
#             "lon_idx": int(lon_idx),
#             "grid_latitude": float(grid_lat),
#             "grid_longitude": float(grid_lon),
#             "distance_km": float(distance),
#             "grid_id": f"P_{lat_idx:02d}_{lon_idx:02d}"
#         }