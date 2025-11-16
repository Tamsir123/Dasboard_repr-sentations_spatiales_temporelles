#!/usr/bin/env python3
"""
Script de conversion NetCDF vers CSV pour le dashboard climatique
Convertit les fichiers NetCDF volumineux en CSV compacts pour une visualisation rapide
"""

import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_netcdf_to_csv(netcdf_path, output_dir=None):
    """
    Convertit un fichier NetCDF en CSV optimisé
    
    Args:
        netcdf_path (str): Chemin vers le fichier NetCDF
        output_dir (str): Répertoire de sortie (par défaut: même répertoire)
    
    Returns:
        str: Chemin vers le fichier CSV créé
    """
    try:
        netcdf_path = Path(netcdf_path)
        if output_dir is None:
            output_dir = netcdf_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📂 Lecture du fichier NetCDF: {netcdf_path}")
        
        # Charger le dataset NetCDF
        ds = xr.open_dataset(netcdf_path)
        
        # Obtenir des informations sur le dataset
        logger.info(f"📊 Dimensions: {dict(ds.dims)}")
        logger.info(f"📋 Variables: {list(ds.data_vars)}")
        
        # Identifier la variable principale (température)
        temp_var = None
        for var_name in ds.data_vars:
            if any(temp_keyword in var_name.lower() for temp_keyword in ['temp', 'tas', 'temperature']):
                temp_var = var_name
                break
        
        if temp_var is None:
            # Prendre la première variable de données
            temp_var = list(ds.data_vars)[0]
        
        logger.info(f"🌡️ Variable de température détectée: {temp_var}")
        
        # Convertir en DataFrame
        logger.info("🔄 Conversion en DataFrame...")
        df = ds[temp_var].to_dataframe().reset_index()
        
        # Nettoyer les données
        logger.info("🧹 Nettoyage des données...")
        
        # Supprimer les valeurs NaN
        initial_size = len(df)
        df = df.dropna()
        final_size = len(df)
        logger.info(f"📉 Suppression de {initial_size - final_size} lignes NaN ({final_size} lignes conservées)")
        
        # Arrondir les valeurs numériques pour réduire la taille
        if 'lat' in df.columns:
            df['lat'] = df['lat'].round(4)
        if 'lon' in df.columns:
            df['lon'] = df['lon'].round(4)
        if temp_var in df.columns:
            df[temp_var] = df[temp_var].round(2)
        
        # Optimiser les types de données
        logger.info("⚡ Optimisation des types de données...")
        
        # Optimiser les coordonnées
        if 'lat' in df.columns:
            df['lat'] = df['lat'].astype('float32')
        if 'lon' in df.columns:
            df['lon'] = df['lon'].astype('float32')
        
        # Optimiser la variable de température
        if temp_var in df.columns:
            df[temp_var] = df[temp_var].astype('float32')
        
        # Créer le nom de fichier de sortie
        csv_filename = netcdf_path.stem + '_optimized.csv'
        csv_path = output_dir / csv_filename
        
        # Sauvegarder en CSV
        logger.info(f"💾 Sauvegarde en CSV: {csv_path}")
        df.to_csv(csv_path, index=False, float_format='%.4f')
        
        # Statistiques finales
        original_size = netcdf_path.stat().st_size / (1024 * 1024)  # MB
        csv_size = csv_path.stat().st_size / (1024 * 1024)  # MB
        compression_ratio = (1 - csv_size / original_size) * 100
        
        logger.info(f"📈 Statistiques de conversion:")
        logger.info(f"   • Fichier original: {original_size:.1f} MB")
        logger.info(f"   • Fichier CSV: {csv_size:.1f} MB")
        logger.info(f"   • Réduction de taille: {compression_ratio:.1f}%")
        logger.info(f"   • Nombre de lignes: {len(df):,}")
        logger.info(f"   • Période: {df['time'].min()} à {df['time'].max()}")
        
        # Fermer le dataset
        ds.close()
        
        return str(csv_path)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la conversion: {e}")
        raise

def create_summary_csv(csv_files, output_path):
    """
    Crée un fichier CSV de résumé avec les statistiques par localité
    
    Args:
        csv_files (list): Liste des fichiers CSV
        output_path (str): Chemin de sortie pour le fichier de résumé
    """
    try:
        logger.info("📊 Création du fichier de résumé...")
        
        all_data = []
        
        for csv_file in csv_files:
            logger.info(f"   • Traitement: {Path(csv_file).name}")
            df = pd.read_csv(csv_file)
            
            # Identifier la variable de température
            temp_cols = [col for col in df.columns if col not in ['lat', 'lon', 'time']]
            temp_var = temp_cols[0] if temp_cols else None
            
            if temp_var:
                # Calculer les statistiques par point de grille
                stats = df.groupby(['lat', 'lon'])[temp_var].agg([
                    'mean', 'min', 'max', 'std', 'count'
                ]).reset_index()
                
                stats['variable'] = temp_var
                stats['source_file'] = Path(csv_file).stem
                all_data.append(stats)
        
        if all_data:
            # Combiner toutes les statistiques
            summary_df = pd.concat(all_data, ignore_index=True)
            
            # Sauvegarder
            summary_df.to_csv(output_path, index=False, float_format='%.4f')
            logger.info(f"✅ Fichier de résumé créé: {output_path}")
            
            return output_path
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du résumé: {e}")
        raise

def main():
    """Fonction principale"""
    # Utiliser le répertoire data spécifié
    data_dir = Path("/home/tamsir/Desktop/Dasboard/backend dasboard climatique/data")
    
    # Créer le répertoire data s'il n'existe pas
    if not data_dir.exists():
        logger.info(f"📁 Création du répertoire de données: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📂 Utilisation du répertoire de données: {data_dir}")
    
    # Trouver tous les fichiers NetCDF
    netcdf_files = list(data_dir.glob("*.nc"))
    
    if not netcdf_files:
        logger.error("❌ Aucun fichier NetCDF trouvé")
        return
    
    logger.info(f"🔍 Fichiers NetCDF trouvés: {len(netcdf_files)}")
    for file in netcdf_files:
        logger.info(f"   • {file.name}")
    
    # Créer le répertoire de sortie dans le même répertoire data
    csv_dir = data_dir / "csv_optimized"
    csv_dir.mkdir(exist_ok=True)
    logger.info(f"📁 Répertoire CSV de sortie: {csv_dir}")
    
    csv_files = []
    
    # Convertir chaque fichier NetCDF
    for netcdf_file in netcdf_files:
        try:
            logger.info(f"\n🚀 Conversion de {netcdf_file.name}...")
            csv_file = convert_netcdf_to_csv(netcdf_file, csv_dir)
            csv_files.append(csv_file)
            logger.info(f"✅ Conversion réussie!")
            
        except Exception as e:
            logger.error(f"❌ Échec de la conversion de {netcdf_file.name}: {e}")
            continue
    
    # Créer un fichier de résumé
    if csv_files:
        summary_path = csv_dir / "climate_summary.csv"
        try:
            create_summary_csv(csv_files, summary_path)
        except Exception as e:
            logger.error(f"❌ Échec de la création du résumé: {e}")
    
    logger.info(f"\n🎉 Conversion terminée!")
    logger.info(f"📁 Fichiers CSV disponibles dans: {csv_dir}")
    logger.info(f"📊 Nombre de fichiers convertis: {len(csv_files)}")

if __name__ == "__main__":
    main()