#!/usr/bin/env python3
"""
Script d'analyse des données NetCDF pour extraire les coordonnées
et identifier les localités potentielles du Sénégal
"""

import sys
import os
sys.path.append('/home/tamsir/Desktop/Dasboard/backend dasboard climatique')

import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path

def analyze_coordinates():
    """Analyse COMPLÈTE des coordonnées disponibles dans les données NetCDF"""
    
    # Chemins des fichiers
    data_dir = Path("/home/tamsir/Desktop/Dasboard/backend dasboard climatique/data")
    tasmin_path = data_dir / "tasmin_daily_Senegal_1960_2024.nc"
    tasmax_path = data_dir / "tasmax_daily_Senegal_1960_2024.nc"
    
    print("📍 Analyse COMPLÈTE des coordonnées NetCDF")
    print("=" * 60)
    
    # Vérifier les deux fichiers
    files_to_check = [
        ("TASMIN", tasmin_path),
        ("TASMAX", tasmax_path)
    ]
    
    all_coords = {}
    
    for file_type, file_path in files_to_check:
        print(f"\n📂 Chargement {file_type}: {file_path.name}")
        
        if not file_path.exists():
            print(f"❌ Fichier non trouvé: {file_path}")
            continue
        
        # Charger le dataset
        ds = xr.open_dataset(file_path)
        
        # Extraire les coordonnées
        latitudes = ds.latitude.values
        longitudes = ds.longitude.values
        
        all_coords[file_type] = {
            'latitudes': latitudes,
            'longitudes': longitudes,
            'dataset': ds
        }
        
        print(f"   ✅ {file_type}: {len(latitudes)} lat × {len(longitudes)} lon = {len(latitudes) * len(longitudes)} points")
        
        ds.close()
    
    # Utiliser les coordonnées du premier fichier disponible pour l'analyse
    if not all_coords:
        print("❌ Aucun fichier NetCDF trouvé!")
        return
    
    # Prendre le premier fichier disponible
    first_key = list(all_coords.keys())[0]
    latitudes = all_coords[first_key]['latitudes']
    longitudes = all_coords[first_key]['longitudes']
    
    print(f"\n📊 Informations détaillées sur les coordonnées ({first_key}):")
    print(f"   Latitudes: {len(latitudes)} points")
    print(f"   Range lat: {latitudes.min():.3f} à {latitudes.max():.3f}")
    print(f"   Longitudes: {len(longitudes)} points") 
    print(f"   Range lon: {longitudes.min():.3f} à {longitudes.max():.3f}")
    
    # Convertir les longitudes (0-360 vers -180-180)
    longitudes_converted = np.where(longitudes > 180, longitudes - 360, longitudes)
    print(f"   Range lon convertie: {longitudes_converted.min():.3f} à {longitudes_converted.max():.3f}")
    
    # Créer une grille de points
    print(f"\n🗺️  Grille de données:")
    print(f"   Résolution lat: ~{(latitudes.max() - latitudes.min()) / (len(latitudes)-1):.3f}°")
    print(f"   Résolution lon: ~{(longitudes_converted.max() - longitudes_converted.min()) / (len(longitudes)-1):.3f}°")
    print(f"   Total points: {len(latitudes) * len(longitudes)} points de grille")
    
    # Afficher TOUS les points de la grille
    print(f"\n📋 TOUS LES POINTS DE LA GRILLE:")
    print("-" * 80)
    
    all_grid_points = []
    for i, lat in enumerate(latitudes):
        for j, lon in enumerate(longitudes):
            lon_conv = longitudes_converted[j]
            all_grid_points.append({
                'grid_id': f"P_{i:02d}_{j:02d}",
                'lat_idx': i,
                'lon_idx': j,
                'latitude': lat,
                'longitude': lon_conv,
                'longitude_original': lon
            })
            
            # Afficher les premiers 50 points pour avoir une idée
            if len(all_grid_points) <= 50:
                print(f"   Point {i:2d},{j:2d}: lat={lat:6.3f}, lon={lon_conv:7.3f} (orig: {lon:6.3f})")
    
    print(f"\n   ... et {len(all_grid_points) - 50} autres points")
    print(f"   📊 Total: {len(all_grid_points)} points de grille disponibles")
    
    # Localités connues du Sénégal (approximatives)
    senegal_cities = {
        "Dakar": (14.6928, -17.4467),
        "Kaolack": (14.1593, -16.0726),
        "Saint-Louis": (16.0333, -16.5000),
        "Thiès": (14.7886, -16.9260),
        "Ziguinchor": (12.5833, -16.2667),
        "Diourbel": (14.6596, -16.2335),
        "Tambacounda": (13.7671, -13.6681),
        "Fatick": (14.3347, -16.4069),
        "Kolda": (12.8939, -14.9422),
        "Matam": (15.6554, -13.2557),
        "Kédougou": (12.5575, -12.1756),
        "Sédhiou": (12.7086, -15.5569),
        "Louga": (15.6186, -16.2284),
        "Kaffrine": (14.1059, -15.5500),
        "Touba": (14.8500, -15.8833)
    }
    
    # Trouver les points de grille les plus proches de chaque ville
    print(f"\n🏘️  Localités et points de grille les plus proches:")
    print("-" * 60)
    
    closest_points = []
    
    for city_name, (city_lat, city_lon) in senegal_cities.items():
        # Trouver le point de grille le plus proche
        lat_diff = np.abs(latitudes - city_lat)
        lon_diff = np.abs(longitudes_converted - city_lon)
        
        lat_idx = np.argmin(lat_diff)
        lon_idx = np.argmin(lon_diff)
        
        grid_lat = latitudes[lat_idx]
        grid_lon = longitudes_converted[lon_idx]
        
        # Calculer la distance
        distance_km = haversine_distance(city_lat, city_lon, grid_lat, grid_lon)
        
        closest_points.append({
            "city": city_name,
            "city_lat": city_lat,
            "city_lon": city_lon,
            "grid_lat": grid_lat,
            "grid_lon": grid_lon,
            "lat_idx": int(lat_idx),
            "lon_idx": int(lon_idx),
            "distance_km": distance_km
        })
        
        print(f"{city_name:15} | "
              f"Ville: ({city_lat:6.3f}, {city_lon:7.3f}) | "
              f"Grille: ({grid_lat:6.3f}, {grid_lon:7.3f}) | "
              f"Distance: {distance_km:5.1f} km")
    
    # Sauvegarder les villes principales
    df_cities = pd.DataFrame(closest_points)
    cities_file = data_dir / "senegal_cities.csv"
    df_cities.to_csv(cities_file, index=False)
    
    # Sauvegarder TOUS les points de grille
    df_all_points = pd.DataFrame(all_grid_points)
    grid_file = data_dir / "senegal_grid_points.csv"
    df_all_points.to_csv(grid_file, index=False)
    
    print(f"\n💾 Fichiers sauvegardés:")
    print(f"   🏘️  Villes principales: {cities_file}")
    print(f"   🗺️  Tous les points: {grid_file}")
    
    # Statistiques finales
    print(f"\n� RÉSUMÉ COMPLET:")
    print(f"   🏘️  Villes prédéfinies: {len(closest_points)}")
    print(f"   🗺️  Points de grille totaux: {len(all_grid_points)}")
    print(f"   📐 Dimensions: {len(latitudes)} lat × {len(longitudes)} lon")
    print(f"   🌍 Zone couverte: {latitudes.min():.1f}°N à {latitudes.max():.1f}°N")
    print(f"                    {longitudes_converted.min():.1f}°W à {longitudes_converted.max():.1f}°W")
    
    return {
        'cities': closest_points,
        'all_points': all_grid_points,
        'grid_dimensions': (len(latitudes), len(longitudes))
    }

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcule la distance haversine entre deux points en km"""
    R = 6371  # Rayon de la Terre en km
    
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c

if __name__ == "__main__":
    try:
        results = analyze_coordinates()
        print(f"\n✅ Analyse complète terminée avec succès!")
        if isinstance(results, dict):
            print(f"   🏘️  {len(results['cities'])} villes principales")
            print(f"   🗺️  {len(results['all_points'])} points de grille totaux")
            print(f"   📐 Grille: {results['grid_dimensions'][0]} × {results['grid_dimensions'][1]}")
        else:
            print(f"   Résultats: {type(results)}")
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()