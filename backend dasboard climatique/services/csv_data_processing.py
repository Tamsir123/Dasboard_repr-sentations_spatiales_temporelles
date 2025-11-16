import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
from pathlib import Path
from functools import lru_cache
import time

class CSVClimateDataProcessor:
    def __init__(self, data_dir: str = "data"):
        """Processeur de données climatiques optimisé pour les fichiers CSV - CHARGEMENT IMMÉDIAT"""
        # S'assurer d'utiliser le chemin relatif au script
        script_dir = Path(__file__).parent.parent  # Remonter au dossier backend
        self.data_dir = script_dir / data_dir
        self.csv_dir = self.data_dir / "csv_optimized"
        
        # Chemins vers les fichiers CSV optimisés
        self.tasmin_csv = self.csv_dir / "tasmin_daily_Senegal_1960_2024_optimized.csv"
        self.tasmax_csv = self.csv_dir / "tasmax_daily_Senegal_1960_2024_optimized.csv"
        
        self._tasmin_df = None
        self._tasmax_df = None
        
        # Charger immédiatement toutes les données
        if self.tasmin_csv.exists():
            self._tasmin_df = pd.read_csv(self.tasmin_csv)
            self._tasmin_df['time'] = pd.to_datetime(self._tasmin_df['time'])
        else:
            raise FileNotFoundError(f"Fichier tasmin CSV introuvable: {self.tasmin_csv}")
        if self.tasmax_csv.exists():
            self._tasmax_df = pd.read_csv(self.tasmax_csv)
            self._tasmax_df['time'] = pd.to_datetime(self._tasmax_df['time'])
        else:
            raise FileNotFoundError(f"Fichier tasmax CSV introuvable: {self.tasmax_csv}")
        
        # Cache pour les résultats calculés
        self._result_cache = {}
        self._cache_expiry = 3600  # 1 heure
        
        # Initialiser immédiatement les métadonnées de la grille
        self._grid_info = None
        self._get_grid_info()
    
    def _get_cache_key(self, method: str, *args) -> str:
        """Génère une clé de cache unique"""
        return f"{method}_{hash(str(args))}"
    
    def _get_cached_result(self, cache_key: str):
        """Récupère un résultat du cache s'il est valide"""
        if cache_key in self._result_cache:
            result, timestamp = self._result_cache[cache_key]
            if time.time() - timestamp < self._cache_expiry:
                return result
            else:
                del self._result_cache[cache_key]
        return None
    
    def _set_cached_result(self, cache_key: str, result):
        """Met en cache un résultat"""
        self._result_cache[cache_key] = (result, time.time())
    
    def _load_csv_data(self, variable: str) -> pd.DataFrame:
        """Retourne les données CSV déjà chargées (pas de chargement paresseux)"""
        if variable == "tasmin":
            if self._tasmin_df is None:
                raise RuntimeError("Données tasmin non chargées - erreur d'initialisation")
            return self._tasmin_df
        
        elif variable == "tasmax":
            if self._tasmax_df is None:
                raise RuntimeError("Données tasmax non chargées - erreur d'initialisation")
            return self._tasmax_df
        else:
            raise ValueError(f"Variable inconnue: {variable}")
    
    def _get_grid_info(self):
        """Obtient les informations de la grille à partir des DONNÉES COMPLÈTES chargées"""
        if self._grid_info is None:
            # Utiliser TOUTES les données complètes chargées en mémoire (pas d'échantillonnage)
            if self._tasmin_df is None:
                raise RuntimeError("Données tasmin non chargées - impossible de détecter la grille")
            
            # Utiliser toutes les données pour détecter la grille complète
            full_data = self._tasmin_df
            
            unique_lats = sorted(full_data['latitude'].unique())
            unique_lons = sorted(full_data['longitude'].unique())
            
            self._grid_info = {
                "latitudes": unique_lats,
                "longitudes": unique_lons,
                "lat_count": len(unique_lats),
                "lon_count": len(unique_lons),
                "lat_range": [min(unique_lats), max(unique_lats)],
                "lon_range": [min(unique_lons), max(unique_lons)]
            }
        
        return self._grid_info
    
    def get_available_variables(self) -> List[str]:
        """Retourne la liste des variables disponibles"""
        return ["tasmin", "tasmax"]
    
    def get_time_range(self) -> Dict[str, int]:
        """Retourne la plage temporelle disponible à partir des données chargées"""
        # Utiliser les données déjà chargées en mémoire
        start_year = self._tasmin_df['time'].dt.year.min()
        end_year = self._tasmin_df['time'].dt.year.max()
        
        return {"start_year": int(start_year), "end_year": int(end_year)}
    
    @lru_cache(maxsize=1)
    def get_available_years(self) -> List[int]:
        """Retourne rapidement la liste de toutes les années disponibles à partir des données chargées"""
        # Utiliser les données déjà chargées en mémoire
        unique_years = sorted(self._tasmin_df['time'].dt.year.unique())
        return unique_years
    
    def get_time_series(self, variable: str, start_year: int, end_year: int) -> Dict:
        """Calcule la série temporelle moyenne annuelle - UTILISE TOUTES LES DONNÉES"""
        cache_key = self._get_cache_key("time_series", variable, start_year, end_year)
        
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Utiliser TOUTES les données complètes chargées
        df = self._load_csv_data(variable)
        # Filtrer par période (utilise toutes les données de la période)
        df_filtered = df[(df['time'].dt.year >= start_year) & (df['time'].dt.year <= end_year)].copy()
        
        # Ajouter une colonne année
        df_filtered['year'] = df_filtered['time'].dt.year
        
        # Calculer la moyenne annuelle sur TOUTES les données
        annual_mean = df_filtered.groupby('year')[variable].mean()
        
        result = {
            "variable": variable,
            "start_year": start_year,
            "end_year": end_year,
            "years": annual_mean.index.tolist(),
            "values": annual_mean.values.tolist(),
            "unit": "°C",
            "data_points_used": len(df_filtered)
        }
        
        self._set_cached_result(cache_key, result)
        return result
    
    def get_climatology(self, variable: str, start_year: int, end_year: int) -> Dict:
        """Calcule la climatologie mensuelle moyenne - UTILISE TOUTES LES DONNÉES"""
        cache_key = self._get_cache_key("climatology", variable, start_year, end_year)
        
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Utiliser TOUTES les données complètes chargées
        df = self._load_csv_data(variable)
        # Filtrer par période (utilise toutes les données de la période)
        df_filtered = df[(df['time'].dt.year >= start_year) & (df['time'].dt.year <= end_year)].copy()
        
        # Ajouter une colonne mois
        df_filtered['month'] = df_filtered['time'].dt.month
        
        # Calculer la climatologie mensuelle sur TOUTES les données
        monthly_mean = df_filtered.groupby('month')[variable].mean()
        
        result = {
            "variable": variable,
            "start_year": start_year,
            "end_year": end_year,
            "months": monthly_mean.index.tolist(),
            "values": monthly_mean.values.tolist(),
            "unit": "°C",
            "data_points_used": len(df_filtered)
        }
        
        self._set_cached_result(cache_key, result)
        return result
    
    def get_spatial_data(self, variable: str, month: int, start_year: int, end_year: int) -> Dict:
        """Retourne les données spatiales pour un mois donné - UTILISE TOUTES LES DONNÉES"""
        cache_key = self._get_cache_key("spatial", variable, month, start_year, end_year)
        
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Utiliser TOUTES les données complètes chargées
        df = self._load_csv_data(variable)
        
        # Filtrer par période et mois (utilise toutes les données correspondantes)
        df_filtered = df[
            (df['time'].dt.year >= start_year) & 
            (df['time'].dt.year <= end_year) &
            (df['time'].dt.month == month)
        ].copy()
        
        # Calculer la moyenne par point de grille sur TOUTES les données
        spatial_mean = df_filtered.groupby(['latitude', 'longitude'])[variable].mean().reset_index()
        
        # Organiser en grille complète
        grid_info = self._get_grid_info()
        
        result = {
            "variable": variable,
            "month": month,
            "start_year": start_year,
            "end_year": end_year,
            "latitudes": grid_info["latitudes"],
            "longitudes": grid_info["longitudes"],
            "data": spatial_mean.to_dict('records'),
            "unit": "°C",
            "data_points_used": len(df_filtered),
            "grid_points_calculated": len(spatial_mean)
        }
        
        self._set_cached_result(cache_key, result)
        return result
    
    def get_statistics(self, variable: str, start_year: int, end_year: int) -> Dict:
        """Calcule les statistiques globales - UTILISE TOUTES LES DONNÉES"""
        cache_key = self._get_cache_key("statistics", variable, start_year, end_year)
        
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Utiliser TOUTES les données complètes chargées
        df = self._load_csv_data(variable)
        
        # Filtrer par période (utilise toutes les données de la période)
        df_filtered = df[(df['time'].dt.year >= start_year) & (df['time'].dt.year <= end_year)]
        
        # Calculer les statistiques sur TOUTES les données
        stats = df_filtered[variable].describe()
        
        result = {
            "variable": variable,
            "start_year": start_year,
            "end_year": end_year,
            "mean": float(stats['mean']),
            "min": float(stats['min']),
            "max": float(stats['max']),
            "std": float(stats['std']),
            "count": int(stats['count']),
            "unit": "°C",
            "data_points_used": len(df_filtered)
        }
        
        self._set_cached_result(cache_key, result)
        return result
    
    def export_data_csv(self, variable: str, start_year: int, end_year: int) -> str:
        """Exporte TOUTES les données CSV pour la période demandée"""
        # Utiliser TOUTES les données complètes chargées
        df = self._load_csv_data(variable)
        
        # Filtrer par période (utilise toutes les données de la période)
        df_filtered = df[(df['time'].dt.year >= start_year) & (df['time'].dt.year <= end_year)]
        
        # Créer le fichier de sortie
        output_file = self.data_dir / f"{variable}_{start_year}_{end_year}_export.csv"
        df_filtered.to_csv(output_file, index=False)
        
        return str(output_file)
    
    def get_locality_data_csv(self, variable: str, lat_idx: int, lon_idx: int, 
                             start_year: int, end_year: int) -> str:
        """Récupère TOUTES les données pour une localité spécifique au format CSV"""
        cache_key = self._get_cache_key("locality_csv", variable, lat_idx, lon_idx, start_year, end_year)
        
        # Utiliser TOUTES les données complètes chargées
        df = self._load_csv_data(variable)
        
        # Obtenir les coordonnées de la grille
        grid_info = self._get_grid_info()
        
        if lat_idx >= len(grid_info["latitudes"]) or lon_idx >= len(grid_info["longitudes"]):
            raise ValueError(f"Indices de grille invalides: lat_idx={lat_idx}, lon_idx={lon_idx}")
        
        target_lat = grid_info["latitudes"][lat_idx]
        target_lon = grid_info["longitudes"][lon_idx]
        
        # Filtrer par localité et période (utilise toutes les données correspondantes)
        locality_data = df[
            (df['latitude'] == target_lat) & 
            (df['longitude'] == target_lon) &
            (df['time'].dt.year >= start_year) & 
            (df['time'].dt.year <= end_year)
        ].copy()
        
        if locality_data.empty:
            raise ValueError(f"Aucune donnée trouvée pour lat_idx={lat_idx}, lon_idx={lon_idx}")
        
        
        # Formater pour l'export CSV
        locality_data['date'] = locality_data['time'].dt.strftime('%Y-%m-%d')
        locality_data['year'] = locality_data['time'].dt.year
        locality_data['month'] = locality_data['time'].dt.month
        locality_data['day'] = locality_data['time'].dt.day
        
        # Sélectionner et réorganiser les colonnes
        export_columns = ['date', 'year', 'month', 'day', 'latitude', 'longitude', variable]
        export_data = locality_data[export_columns].copy()
        
        # Convertir en CSV string
        csv_string = export_data.to_csv(index=False, float_format='%.2f')
        
        return csv_string
    
    def find_nearest_grid_point(self, target_lat: float, target_lon: float) -> Dict:
        """Trouve le point de grille le plus proche des coordonnées données"""
        grid_info = self._get_grid_info()
        
        # Convertir en arrays numpy pour le calcul
        lats = np.array(grid_info["latitudes"])
        lons = np.array(grid_info["longitudes"])
        
        # Trouver les indices les plus proches
        lat_idx = np.argmin(np.abs(lats - target_lat))
        lon_idx = np.argmin(np.abs(lons - target_lon))
        
        # Calculer la distance
        actual_lat = lats[lat_idx]
        actual_lon = lons[lon_idx]
        distance = np.sqrt((target_lat - actual_lat)**2 + (target_lon - actual_lon)**2) * 111  # km
        
        return {
            "lat_idx": int(lat_idx),
            "lon_idx": int(lon_idx),
            "grid_latitude": float(actual_lat),
            "grid_longitude": float(actual_lon),
            "distance_km": float(distance),
            "target_latitude": target_lat,
            "target_longitude": target_lon
        }
    
    def get_available_localities(self) -> Dict:
        """Retourne les informations sur les localités disponibles"""
        grid_info = self._get_grid_info()
        
        # Villes principales du Sénégal avec leurs coordonnées
        cities = [
            {"name": "Dakar", "latitude": 14.7167, "longitude": -17.4677},
            {"name": "Thiès", "latitude": 14.7886, "longitude": -16.9260},
            {"name": "Kaolack", "latitude": 14.1612, "longitude": -16.0734},
            {"name": "Saint-Louis", "latitude": 16.0469, "longitude": -16.4814},
            {"name": "Ziguinchor", "latitude": 12.5681, "longitude": -16.2736},
            {"name": "Diourbel", "latitude": 14.6594, "longitude": -16.2353},
            {"name": "Tambacounda", "latitude": 13.7671, "longitude": -13.6681},
            {"name": "Kolda", "latitude": 12.8939, "longitude": -14.9406},
            {"name": "Fatick", "latitude": 14.3341, "longitude": -16.4069},
            {"name": "Louga", "latitude": 15.6181, "longitude": -16.2463},
            {"name": "Matam", "latitude": 15.6554, "longitude": -13.2550},
            {"name": "Kaffrine", "latitude": 14.1058, "longitude": -15.5500},
            {"name": "Kédougou", "latitude": 12.5601, "longitude": -12.1756},
            {"name": "Sédhiou", "latitude": 12.7081, "longitude": -15.5569},
            {"name": "Mbour", "latitude": 14.4198, "longitude": -16.9613}
        ]
        
        # Ajouter les informations de grille pour chaque ville
        for city in cities:
            grid_point = self.find_nearest_grid_point(city["latitude"], city["longitude"])
            city.update(grid_point)
        
        return {
            "cities": cities,
            "grid_summary": {
                "total_points": grid_info["lat_count"] * grid_info["lon_count"],
                "latitudes_count": grid_info["lat_count"],
                "longitudes_count": grid_info["lon_count"],
                "lat_range": grid_info["lat_range"],
                "lon_range": grid_info["lon_range"]
            }
        }

# Classe de compatibilité pour maintenir l'interface existante
class ClimateDataProcessor(CSVClimateDataProcessor):
    """Version de compatibilité qui utilise les CSV optimisés"""
    
    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
    
    def export_data(self, variable: str, start_year: int, end_year: int, format_type: str = "csv") -> str:
        """Export compatible avec l'ancienne interface"""
        if format_type == "csv":
            return self.export_data_csv(variable, start_year, end_year)
        else:
            raise ValueError(f"Format {format_type} non supporté en mode CSV optimisé")
    
    def get_locality_time_series(self, variable: str, lat_idx: int, lon_idx: int, 
                                start_year: int, end_year: int) -> Dict:
        """Interface de compatibilité pour les séries temporelles de localité"""
        # Utiliser les données CSV pour calculer la série temporelle
        csv_data = self.get_locality_data_csv(variable, lat_idx, lon_idx, start_year, end_year)
        
        # Parser le CSV pour extraire les données
        import io
        df = pd.read_csv(io.StringIO(csv_data))
        
        # Calculer la moyenne annuelle
        annual_mean = df.groupby('year')[variable].mean()
        
        grid_info = self._get_grid_info()
        
        return {
            "variable": variable,
            "lat_idx": lat_idx,
            "lon_idx": lon_idx,
            "latitude": grid_info["latitudes"][lat_idx],
            "longitude": grid_info["longitudes"][lon_idx],
            "start_year": start_year,
            "end_year": end_year,
            "years": annual_mean.index.tolist(),
            "values": annual_mean.values.tolist(),
            "unit": "°C"
        }