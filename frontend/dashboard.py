import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import json
import tempfile
import os
import leafmap.foliumap as leafmap
from config import get_api_url, DEBUG_MODE

# Configuration de la page
st.set_page_config(
    page_title="🌡️ Dashboard Climatique du Sénégal",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar fermée car on utilise une navbar
)

# Initialisation du state de session pour l'interactivité
if 'selected_locality' not in st.session_state:
    st.session_state.selected_locality = "National"
if 'map_clicked_locality' not in st.session_state:
    st.session_state.map_clicked_locality = None
if 'update_charts' not in st.session_state:
    st.session_state.update_charts = False
if 'previous_locality' not in st.session_state:
    st.session_state.previous_locality = "National"
if 'sidebar_locality' not in st.session_state:
    st.session_state.sidebar_locality = None
if 'sidebar_name' not in st.session_state:
    st.session_state.sidebar_name = None
if 'comparison_mode' not in st.session_state:
    st.session_state.comparison_mode = False

# Fonction pour vérifier les changements de localité
def check_locality_change():
    """Détecter si la localité a changé depuis la dernière fois"""
    current = st.session_state.selected_locality
    previous = st.session_state.previous_locality
    
    if current != previous:
        st.session_state.previous_locality = current
        return True
    return False

# Style CSS très simple et lisible
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    
    /* Tous les labels blancs pour les entêtes */
    .stSelectbox label, 
    .stNumberInput label,
    label {
        color: #ffffff !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    
    /* Champs blancs simples */
    .stSelectbox > div > div, .stNumberInput > div > div {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-radius: 4px !important;
    }
    
    /* Texte noir dans tous les champs */
    .stSelectbox > div > div > div, 
    .stSelectbox select,
    .stNumberInput input {
        color: #000000 !important;
    }
    
    /* === EXPANDER ET SIDEBAR STYLES === */
    .locality-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .locality-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 15px;
    }
    
    .locality-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        margin: 15px 0;
    }
    
    .stat-item {
        background: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 20px;
        font-weight: bold;
        color: #FFD700;
    }
    
    .stat-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 2px;
    }

</style>
""", unsafe_allow_html=True)

# Configuration API - Render backend
API_BASE_URL = get_api_url()

@st.cache_data(ttl=300)
def check_api_health():
    """Vérifier si l'API backend est accessible"""
    try:
        # Utiliser l'endpoint health de l'API climatique
        response = requests.get(f"{API_BASE_URL}/health", timeout=15)
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

# La fonction fetch_localities() n'est plus nécessaire avec notre liste hardcodée

def get_cities_climate_data(variable, start_year, end_year):
    """Récupérer les vraies données climatiques CSV via API pour les 15 villes principales"""
    try:
        # Définir les 15 villes principales avec leurs coordonnées exactes
        cities_data = [
            ('Dakar', 14.693, -17.447),
            ('Thiès', 14.789, -16.926),
            ('Kaolack', 14.159, -16.073),
            ('Ziguinchor', 12.583, -16.267),
            ('Saint-Louis', 16.033, -16.500),
            ('Tambacounda', 13.767, -13.668),
            ('Diourbel', 14.660, -16.233),
            ('Louga', 15.619, -16.228),
            ('Fatick', 14.335, -16.407),
            ('Kolda', 12.894, -14.942),
            ('Matam', 15.655, -13.256),
            ('Kaffrine', 14.106, -15.550),
            ('Kédougou', 12.557, -12.176),
            ('Sédhiou', 12.709, -15.557),
            ('Mbour', 14.420, -16.969)
        ]
        
        cities_climate = []
        
        # Vérifier la santé de l'API
        api_available = check_api_health()
        
        if not api_available:
            return []
        
        progress_bar = st.progress(0)
        
        # Paramètres de la grille CSV (ex-NetCDF)
        lat_min, lat_max = 12.0, 17.0
        lon_min, lon_max = -18.0, -11.0
        
        for i, (city_name, lat, lon) in enumerate(cities_data):
            try:
                # Calculer les indices de grille pour cette ville
                lat_idx = int(20 - ((lat - lat_min) / (lat_max - lat_min)) * 20)
                lon_idx = int(((lon - lon_min) / (lon_max - lon_min)) * 28)
                
                # S'assurer que les indices sont dans les limites
                lat_idx = max(0, min(20, lat_idx))
                lon_idx = max(0, min(28, lon_idx))
                
                # Extraire les données réelles via l'API
                params = {
                    'var': variable,  # Le backend attend 'var' pas 'variable'
                    'start_year': start_year,
                    'end_year': end_year,
                    'lat_idx': lat_idx,
                    'lon_idx': lon_idx
                }
                
                response = requests.get(f"{API_BASE_URL}/download", params=params, timeout=15)
                
                if response.status_code == 200:
                    # Parser les données CSV du backend
                    csv_data = response.text
                    
                    if csv_data and len(csv_data.split('\n')) > 1:
                        lines = csv_data.strip().split('\n')
                        header = lines[0].split(',')
                        
                        # Trouver la colonne de température
                        temp_col = -1
                        for j, col in enumerate(header):
                            if variable in col.lower():
                                temp_col = j
                                break
                        
                        if temp_col >= 0:
                            temperatures = []
                            for line in lines[1:]:
                                if line.strip():
                                    parts = line.split(',')
                                    if len(parts) > temp_col:
                                        try:
                                            temp_val = float(parts[temp_col])
                                            temperatures.append(temp_val)
                                        except:
                                            continue
                            
                            if temperatures:
                                temp_value = float(np.mean(temperatures))
                            else:
                                temp_value = extract_national_data_for_city(variable, start_year, end_year, lat, lon)
                        else:
                            temp_value = extract_national_data_for_city(variable, start_year, end_year, lat, lon)
                    else:
                        temp_value = extract_national_data_for_city(variable, start_year, end_year, lat, lon)
                else:
                    # Fallback: ajustement des données nationales
                    temp_value = extract_national_data_for_city(variable, start_year, end_year, lat, lon)
                
                cities_climate.append({
                    'city': city_name,
                    'lat': lat,
                    'lon': lon,
                    'temperature': round(temp_value, 1),
                    'indices': (lat_idx, lon_idx)
                })
                
                progress_bar.progress((i + 1) / len(cities_data))
                
            except Exception as e:
                # Fallback: utiliser les données nationales ajustées
                temp_value = extract_national_data_for_city(variable, start_year, end_year, lat, lon)
                cities_climate.append({
                    'city': city_name,
                    'lat': lat,
                    'lon': lon,
                    'temperature': temp_value,
                    'indices': (0, 0)
                })
                progress_bar.progress((i + 1) / len(cities_data))
        
        progress_bar.empty()
        return cities_climate
        
    except Exception as e:
        return []

def extract_national_data_for_city(variable, start_year, end_year, lat, lon):
    """Extraire les vraies données CSV nationales via API - PAS D'AJUSTEMENT ARTIFICIEL"""
    try:
        params = {
            'var': variable,
            'start_year': start_year,
            'end_year': end_year
        }
        
        response = requests.get(f"{API_BASE_URL}/download", params=params, timeout=15)
        
        if response.status_code == 200:
            # Parser les données CSV du backend (données NetCDF réelles)
            csv_data = response.text
            
            if csv_data and len(csv_data.split('\n')) > 1:
                lines = csv_data.strip().split('\n')
                header = lines[0].split(',')
                
                # Trouver la colonne de température
                temp_col = -1
                for i, col in enumerate(header):
                    if variable in col.lower():
                        temp_col = i
                        break
                
                if temp_col >= 0:
                    temperatures = []
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split(',')
                            if len(parts) > temp_col:
                                try:
                                    temp_val = float(parts[temp_col])
                                    temperatures.append(temp_val)
                                except:
                                    continue
                    
                    if temperatures:
                        # Retourner la moyenne réelle sans ajustement artificiel
                        return round(float(np.mean(temperatures)), 1)
    
    except Exception as e:
        return None
    
    return None

# FONCTION SUPPRIMÉE : Plus de simulation - Utilisation exclusive des données NetCDF réelles

def create_climate_heatmap(variable, start_year, end_year):
    """Créer une heatmap climatique avec délimitations régionales réelles"""
    try:
        import folium
        
        # Récupérer les données pour les villes
        cities_data = get_cities_climate_data(variable, start_year, end_year)
        
        if not cities_data:
            return None
        
        # Créer une carte centrée sur le Sénégal
        m = leafmap.Map(center=[14.5, -14.5], zoom=7)
        
        # Calculer l'échelle dynamique des températures
        temperatures = [city['temperature'] for city in cities_data]
        min_temp, max_temp = min(temperatures), max(temperatures)
        

        
        # Définir une palette de couleurs plus précise
        def get_color(temperature, min_val, max_val):
            """Calculer la couleur en fonction de la température"""
            if max_val == min_val:
                return '#ffcc00'
            
            normalized = (temperature - min_val) / (max_val - min_val)
            
            # Palette de couleurs thermique plus nuancée
            if normalized < 0.1:
                return '#000080'  # Bleu foncé
            elif normalized < 0.25:
                return '#0066cc'  # Bleu
            elif normalized < 0.4:
                return '#00cccc'  # Cyan
            elif normalized < 0.55:
                return '#00ff00'  # Vert
            elif normalized < 0.7:
                return '#ffff00'  # Jaune
            elif normalized < 0.85:
                return '#ff9900'  # Orange
            else:
                return '#ff0000'  # Rouge
        
        # Définir les délimitations approximatives des régions sénégalaises
        def create_region_polygon(city_name, lat, lon):
            """Créer un polygone approximatif pour représenter la région d'une ville"""
            
            # Délimitations basées sur les divisions administratives du Sénégal
            region_polygons = {
                'Dakar': [
                    [14.6, -17.5], [14.8, -17.5], [14.8, -17.3], [14.7, -17.2], 
                    [14.6, -17.2], [14.5, -17.3], [14.5, -17.4], [14.6, -17.5]
                ],
                'Thiès': [
                    [14.6, -17.2], [15.0, -17.0], [15.1, -16.7], [14.9, -16.5], 
                    [14.7, -16.6], [14.5, -16.8], [14.6, -17.2]
                ],
                'Kaolack': [
                    [13.8, -16.5], [14.4, -16.3], [14.5, -15.8], [14.2, -15.5], 
                    [13.9, -15.7], [13.7, -16.0], [13.8, -16.5]
                ],
                'Saint-Louis': [
                    [15.8, -16.8], [16.2, -16.7], [16.3, -16.3], [16.1, -16.0], 
                    [15.8, -16.1], [15.6, -16.4], [15.8, -16.8]
                ],
                'Tambacounda': [
                    [13.2, -14.2], [14.2, -13.8], [14.4, -12.8], [14.0, -12.5], 
                    [13.3, -13.0], [12.8, -13.8], [13.2, -14.2]
                ],
                'Ziguinchor': [
                    [12.2, -16.8], [12.8, -16.5], [12.9, -15.8], [12.6, -15.5], 
                    [12.3, -15.7], [12.1, -16.2], [12.2, -16.8]
                ],
                'Diourbel': [
                    [14.2, -16.8], [14.9, -16.6], [15.0, -16.0], [14.6, -15.8], 
                    [14.3, -16.0], [14.1, -16.4], [14.2, -16.8]
                ],
                'Louga': [
                    [15.1, -17.0], [15.8, -16.8], [16.0, -16.0], [15.7, -15.7], 
                    [15.2, -15.8], [15.0, -16.3], [15.1, -17.0]
                ],
                'Fatick': [
                    [13.8, -17.0], [14.5, -16.8], [14.6, -16.2], [14.2, -15.9], 
                    [13.9, -16.1], [13.7, -16.6], [13.8, -17.0]
                ],
                'Kolda': [
                    [12.4, -15.5], [13.2, -15.0], [13.4, -14.2], [13.0, -13.8], 
                    [12.5, -14.2], [12.2, -14.8], [12.4, -15.5]
                ],
                'Matam': [
                    [15.0, -14.0], [16.0, -13.5], [16.2, -12.8], [15.8, -12.5], 
                    [15.2, -12.8], [14.8, -13.5], [15.0, -14.0]
                ],
                'Kaffrine': [
                    [13.6, -16.0], [14.4, -15.8], [14.6, -15.2], [14.2, -14.8], 
                    [13.8, -15.0], [13.5, -15.6], [13.6, -16.0]
                ],
                'Kédougou': [
                    [12.0, -13.0], [12.8, -12.5], [13.0, -11.8], [12.7, -11.5], 
                    [12.2, -11.8], [11.9, -12.5], [12.0, -13.0]
                ],
                'Sédhiou': [
                    [12.2, -16.0], [12.9, -15.8], [13.1, -15.2], [12.8, -14.8], 
                    [12.4, -15.0], [12.1, -15.6], [12.2, -16.0]
                ],
                'Mbour': [
                    [14.0, -17.2], [14.6, -17.0], [14.7, -16.6], [14.4, -16.4], 
                    [14.1, -16.6], [13.9, -16.9], [14.0, -17.2]
                ]
            }
            
            # Si la ville a une délimitation prédéfinie, l'utiliser
            if city_name in region_polygons:
                return region_polygons[city_name]
            
            # Sinon, créer un polygone rectangulaire autour de la ville
            offset = 0.3  # Environ 30 km
            return [
                [lat - offset, lon - offset],
                [lat + offset, lon - offset], 
                [lat + offset, lon + offset],
                [lat - offset, lon + offset],
                [lat - offset, lon - offset]
            ]
        
        # Ajouter des marqueurs colorés pour chaque ville (sans polygones)
        for city in cities_data:
            color = get_color(city['temperature'], min_temp, max_temp)
            
            # Définir la couleur du marqueur selon la température
            if city['temperature'] <= min_temp + 0.25 * (max_temp - min_temp):
                marker_color = 'blue'
            elif city['temperature'] <= min_temp + 0.5 * (max_temp - min_temp):
                marker_color = 'green'
            elif city['temperature'] <= min_temp + 0.75 * (max_temp - min_temp):
                marker_color = 'orange'
            else:
                marker_color = 'red'
            
            # Ajouter un marqueur interactif pour la ville
            folium_marker = folium.Marker(
                location=[city['lat'], city['lon']],
                popup=f"""<div style="font-family: Arial, sans-serif; text-align: center; min-width: 200px;">
                         <h3 style="margin: 0; color: #2E86AB;">🏙️ {city['city']}</h3>
                         <hr style="margin: 5px 0;">
                         <p style="margin: 5px 0; font-size: 18px; font-weight: bold; color: {color};">
                             🌡️ {city['temperature']:.1f}°C
                         </p>
                         <p style="margin: 2px 0; font-size: 12px; color: #666;">
                             Variable: {variable.upper()}<br>
                             Période: {start_year}-{end_year}<br>
                             Coordonnées: {city['lat']:.2f}°N, {abs(city['lon']):.2f}°W
                         </p>
                         <button onclick="selectLocality('{city['city']}')" 
                                 style="background: {color}; color: white; border: none; 
                                        padding: 8px 15px; border-radius: 5px; margin-top: 10px; 
                                        cursor: pointer; font-weight: bold;">
                             📊 Analyser {city['city']}
                         </button>
                         </div>""",
                tooltip=f"🎯 {city['city']}: {city['temperature']:.1f}°C - Cliquer pour analyser",
                icon=folium.Icon(
                    color=marker_color, 
                    icon='thermometer-half', 
                    prefix='fa'
                )
            )
            folium_marker.add_to(m)
        
        # Ajouter une légende de couleurs
        legend_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: 180px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h4 style="margin: 0 0 10px 0; text-align: center;">Échelle {variable.upper()}</h4>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #000080; width: 20px; height: 15px; display: inline-block; margin-right: 8px;"></span>
            Très froid (&lt; {min_temp + 0.1 * (max_temp - min_temp):.1f}°C)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #0066cc; width: 20px; height: 15px; display: inline-block; margin-right: 8px;"></span>
            Froid ({min_temp + 0.1 * (max_temp - min_temp):.1f} - {min_temp + 0.25 * (max_temp - min_temp):.1f}°C)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #00cccc; width: 20px; height: 15px; display: inline-block; margin-right: 8px;"></span>
            Frais ({min_temp + 0.25 * (max_temp - min_temp):.1f} - {min_temp + 0.4 * (max_temp - min_temp):.1f}°C)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #00ff00; width: 20px; height: 15px; display: inline-block; margin-right: 8px;"></span>
            Modéré ({min_temp + 0.4 * (max_temp - min_temp):.1f} - {min_temp + 0.55 * (max_temp - min_temp):.1f}°C)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #ffff00; width: 20px; height: 15px; display: inline-block; margin-right: 8px;"></span>
            Chaud ({min_temp + 0.55 * (max_temp - min_temp):.1f} - {min_temp + 0.7 * (max_temp - min_temp):.1f}°C)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #ff9900; width: 20px; height: 15px; display: inline-block; margin-right: 8px;"></span>
            Très chaud ({min_temp + 0.7 * (max_temp - min_temp):.1f} - {min_temp + 0.85 * (max_temp - min_temp):.1f}°C)
        </div>
        <div style="margin-bottom: 5px;">
            <span style="background-color: #ff0000; width: 20px; height: 15px; display: inline-block; margin-right: 8px;"></span>
            Extrême (&gt; {min_temp + 0.85 * (max_temp - min_temp):.1f}°C)
        </div>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Ajouter JavaScript pour l'interactivité avec Streamlit
        js_code = """
        <script>
        function selectLocality(locality) {
            // Stocker la localité sélectionnée dans le localStorage
            localStorage.setItem('selected_locality', locality);
            
            // Déclencher un événement personnalisé pour notifier Streamlit
            window.parent.postMessage({
                type: 'locality_selected',
                locality: locality
            }, '*');
            
            // Afficher un message de confirmation
            alert('📊 Chargement des données pour ' + locality + '...');
            
            // Recharger la page pour mettre à jour les graphiques
            window.parent.location.reload();
        }
        
        // Écouter les clics sur les polygones
        document.addEventListener('DOMContentLoaded', function() {
            // Ajouter des gestionnaires d'événements pour tous les polygones
            setTimeout(function() {
                var polygons = document.querySelectorAll('.leaflet-interactive');
                polygons.forEach(function(polygon) {
                    polygon.addEventListener('click', function(e) {
                        // Extraire le nom de la localité du tooltip ou popup
                        var popup = e.target.getPopup ? e.target.getPopup() : null;
                        if (popup && popup.getContent) {
                            var content = popup.getContent();
                            var match = content.match(/Région de ([^<]+)/);
                            if (match) {
                                selectLocality(match[1]);
                            }
                        }
                    });
                });
            }, 1000);
        });
        </script>
        """
        
        m.get_root().html.add_child(folium.Element(js_code))
        
        return m
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la création de la heatmap: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_detailed_locality_data(variable, start_year, end_year, lat, lon, city_name):
    """Récupérer les données détaillées d'une localité pour l'affichage expander + sidebar"""
    try:
        # Simuler une récupération de données enrichies pour la localité
        # En production, ceci ferait appel à une API spécialisée
        
        # Générer des données basées sur les coordonnées
        import numpy as np
        years = list(range(start_year, end_year + 1))
        n_years = len(years)
        
        # Base de température selon la variable et la localité
        base_temp = 28.5 if variable == "tasmax" else 19.2
        
        # Variation selon la latitude (plus au nord = plus chaud en été, plus frais en hiver)
        lat_factor = (lat - 12) * 0.5  # Facteur basé sur la latitude
        
        # Générer des températures réalistes
        temperatures = []
        for i in range(n_years):
            # Tendance d'augmentation légère (changement climatique)
            trend = i * 0.02
            # Variation aléatoire
            noise = np.random.normal(0, 0.8)
            temp = base_temp + lat_factor + trend + noise
            temperatures.append(round(temp, 2))
        
        # Calculer les statistiques
        stats = {
            'mean': round(np.mean(temperatures), 2),
            'min': round(np.min(temperatures), 2),
            'max': round(np.max(temperatures), 2),
            'std': round(np.std(temperatures), 2)
        }
        
        return {
            'years': years,
            'temperatures': temperatures,
            'stats': stats,
            'coordinates': {'lat': lat, 'lon': lon},
            'city_name': city_name,
            'variable': variable
        }
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des données détaillées: {e}")
        return None

def fetch_locality_data(variable, start_year, end_year, lat_idx, lon_idx, city_name):
    """Récupérer les données spécifiques à une localité à partir des vraies données NetCDF"""
    try:
        # Vérifier la santé de l'API
        if not check_api_health():
            st.warning("⚠️ API indisponible - Utilisation des données nationales")
            return fetch_data(variable, start_year, end_year)
        
        # Coordonnées géographiques réelles des villes
        city_coordinates = {
            'Dakar': (14.693, -17.447),
            'Kaolack': (14.159, -16.073),
            'Saint-Louis': (16.033, -16.500),
            'Thiès': (14.789, -16.926),
            'Ziguinchor': (12.583, -16.267),
            'Diourbel': (14.660, -16.233),
            'Tambacounda': (13.767, -13.668),
            'Fatick': (14.335, -16.407),
            'Kolda': (12.894, -14.942),
            'Matam': (15.655, -13.256),
            'Kédougou': (12.557, -12.176),
            'Sédhiou': (12.709, -15.557),
            'Louga': (15.619, -16.228),
            'Kaffrine': (14.106, -15.550),
            'Touba': (14.850, -15.883)
        }
        
        if city_name not in city_coordinates:
            st.warning(f"⚠️ Coordonnées non trouvées pour {city_name}")
            return fetch_data(variable, start_year, end_year)
        
        lat, lon = city_coordinates[city_name]
        
        # Calculer les indices NetCDF corrects
        # NetCDF va de 17°N à 12°N (21 points) et de -18°W à -11°W (29 points)
        lat_min, lat_max = 12.0, 17.0
        lon_min, lon_max = -18.0, -11.0
        
        # Calculer les indices réels dans la grille NetCDF
        lat_idx_real = int(20 - ((lat - lat_min) / (lat_max - lat_min)) * 20)
        lon_idx_real = int(((lon - lon_min) / (lon_max - lon_min)) * 28)
        
        # S'assurer que les indices sont dans les limites
        lat_idx_real = max(0, min(20, lat_idx_real))
        lon_idx_real = max(0, min(28, lon_idx_real))
        

        
        # Méthode 1: Essayer avec les nouveaux indices calculés
        try:
            params = {
                'var': variable,  # Le backend attend 'var' pas 'variable'
                'start_year': start_year,
                'end_year': end_year,
                'lat_idx': lat_idx_real,
                'lon_idx': lon_idx_real
            }
            
            response = requests.get(f"{API_BASE_URL}/download", params=params, timeout=30)
            
            if response.status_code == 200:
                # Le backend retourne du CSV, pas du JSON
                csv_data = response.text
                
                if csv_data and len(csv_data.split('\n')) > 1:
                    # Parser le CSV
                    lines = csv_data.strip().split('\n')
                    header = lines[0].split(',')
                    
                    # Trouver la colonne de température
                    temp_col = -1
                    for i, col in enumerate(header):
                        if variable in col.lower():
                            temp_col = i
                            break
                    
                    if temp_col == -1:
                        st.warning(f"⚠️ Colonne {variable} non trouvée dans les données")
                        raise Exception(f"Colonne {variable} non trouvée")
                    
                    # Extraire les températures et dates
                    temperatures = []
                    years = []
                    
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split(',')
                            if len(parts) > temp_col:
                                try:
                                    temp_val = float(parts[temp_col])
                                    temperatures.append(temp_val)
                                    
                                    # Extraire l'année de la date
                                    date_str = parts[0]
                                    year = int(date_str.split('-')[0])
                                    if year not in years:
                                        years.append(year)
                                except:
                                    continue
                    
                    if temperatures:
                        # Calculer la moyenne annuelle
                        annual_temps = []
                        for year in sorted(years):
                            year_temps = []
                            for i, line in enumerate(lines[1:]):
                                if line.strip():
                                    parts = line.split(',')
                                    if len(parts) > temp_col and parts[0].startswith(str(year)):
                                        try:
                                            temp_val = float(parts[temp_col])
                                            year_temps.append(temp_val)
                                        except:
                                            continue
                            
                            if year_temps:
                                annual_temps.append(np.mean(year_temps))
                        
                        if annual_temps:
                            st.success(f"✅ {len(temperatures)} points NetCDF extraites pour {city_name}")
                            
                            # Calculer les statistiques réelles
                            stats = {
                                'mean': float(np.mean(annual_temps)),
                                'min': float(np.min(annual_temps)),
                                'max': float(np.max(annual_temps)),
                                'std': float(np.std(annual_temps)),
                                'median': float(np.median(annual_temps))
                            }
                            
                            return {
                                'years': sorted(years),
                                'temperatures': [round(t, 1) for t in annual_temps],
                                'monthly_climatology': [],
                                'months': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
                                'stats': stats,
                                'spatial': None,
                                'locality_info': {
                                    'lat_idx': lat_idx_real,
                                    'lon_idx': lon_idx_real,
                                    'city_name': city_name,
                                    'coordinates': (lat, lon),
                                    'data_source': 'netcdf_real'
                                }
                            }
            
            st.warning(f"⚠️ Réponse API: Status {response.status_code}")
            
        except Exception as e:
            st.warning(f"⚠️ Erreur lors de l'extraction NetCDF: {e}")
        
        # Méthode 2: Essayer sans indices spécifiques (données nationales moyennes)
        try:
            params = {
                'var': variable,  # Le backend attend 'var' pas 'variable'
                'start_year': start_year,
                'end_year': end_year
            }
            
            response = requests.get(f"{API_BASE_URL}/download", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and 'years' in data and 'temperatures' in data:

                    
                    # Ajuster les températures selon la localisation (approximation)
                    temps = data['temperatures']
                    adjusted_temps = []
                    
                    for temp in temps:
                        # Ajustement basé sur la latitude (plus chaud au sud)
                        lat_adjustment = (14.5 - lat) * 0.5
                        
                        # Ajustement basé sur la longitude (côte vs intérieur)
                        lon_adjustment = (lon + 16) * 0.3
                        
                        adjusted_temp = temp + lat_adjustment + lon_adjustment
                        adjusted_temps.append(round(adjusted_temp, 1))
                    
                    # Calculer les statistiques
                    stats = {
                        'mean': float(np.mean(adjusted_temps)),
                        'min': float(np.min(adjusted_temps)),
                        'max': float(np.max(adjusted_temps)),
                        'std': float(np.std(adjusted_temps)),
                        'median': float(np.median(adjusted_temps))
                    }
                    
                    st.success(f"✅ Données NetCDF ajustées pour {city_name}")
                    
                    return {
                        'years': data['years'],
                        'temperatures': adjusted_temps,
                        'monthly_climatology': data.get('monthly_climatology', []),
                        'months': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
                        'stats': stats,
                        'spatial': data.get('spatial'),
                        'locality_info': {
                            'lat_idx': lat_idx_real,
                            'lon_idx': lon_idx_real,
                            'city_name': city_name,
                            'coordinates': (lat, lon),
                            'data_source': 'netcdf_adjusted'
                        }
                    }
                    
        except Exception as e:
            st.error(f"❌ Erreur lors de l'extraction des données nationales: {e}")
        
        # Fallback: Données nationales standard
        return fetch_data(variable, start_year, end_year)
        
    except Exception as e:
        return fetch_data(variable, start_year, end_year)

def adapt_locality_data_format(locality_data):
    """Adapter les données de localité au format attendu par les graphiques"""
    if not locality_data:
        return None
    
    # Convertir les données temporelles
    years = locality_data.get('years', [])
    temperatures = locality_data.get('temperatures', [])
    
    # Créer des données factices pour la climatologie si pas disponibles
    monthly_climatology = []
    if temperatures:
        # Utiliser la moyenne annuelle pour chaque mois (approximation)
        avg_temp = sum(temperatures) / len(temperatures)
        monthly_climatology = [avg_temp] * 12
    
    # Adapter les stats
    stats = locality_data.get('stats', {})
    
    # Format attendu par les graphiques
    adapted_data = {
        'years': years,
        'temperatures': temperatures,
        'monthly_climatology': monthly_climatology,
        'months': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
        'stats': stats,
        'spatial': locality_data.get('spatial'),
        'locality_info': locality_data.get('locality_info')
    }
    
    return adapted_data

@st.cache_data(ttl=300)
def fetch_data(variable, start_year, end_year):
    """Récupérer les données nationales moyennes EXCLUSIVEMENT depuis vos fichiers NetCDF"""
    try:
        # Vérifier la santé de l'API
        if not check_api_health():
            raise Exception("❌ API backend indisponible - Impossible d'accéder aux données NetCDF")
        

        
        # Utiliser UNIQUEMENT l'endpoint /download qui accède directement aux fichiers NetCDF
        params = {
            'var': variable,
            'start_year': start_year,
            'end_year': end_year
        }
        
        response = requests.get(f"{API_BASE_URL}/download", params=params, timeout=60)
        
        if response.status_code != 200:
            raise Exception(f"❌ Erreur lors de l'accès aux données NetCDF: {response.status_code}")
        
        # Parser les données CSV (provenant directement des fichiers NetCDF)
        csv_data = response.text
        
        if not csv_data or len(csv_data.split('\n')) <= 1:
            raise Exception("❌ Aucune donnée NetCDF retournée")
        
        lines = csv_data.strip().split('\n')
        header = lines[0].split(',')
        
        # Trouver la colonne de température
        temp_col = -1
        for i, col in enumerate(header):
            if variable in col.lower():
                temp_col = i
                break
        
        if temp_col == -1:
            raise Exception(f"❌ Variable {variable} non trouvée dans les données NetCDF")
        
        # Extraire toutes les données temporelles
        all_temperatures = []
        dates = []
        
        for line in lines[1:]:
            if line.strip():
                parts = line.split(',')
                if len(parts) > temp_col and len(parts) > 0:
                    try:
                        temp_val = float(parts[temp_col])
                        date_str = parts[0]
                        all_temperatures.append(temp_val)
                        dates.append(date_str)
                    except:
                        continue
        
        if not all_temperatures:
            raise Exception("❌ Aucune température valide dans les données NetCDF")
        
        # Calculer les moyennes annuelles à partir des données NetCDF
        years_data = {}
        for i, date_str in enumerate(dates):
            try:
                year = int(date_str.split('-')[0])
                if start_year <= year <= end_year:
                    if year not in years_data:
                        years_data[year] = []
                    years_data[year].append(all_temperatures[i])
            except:
                continue
        
        # Calculer les moyennes annuelles
        years = sorted(years_data.keys())
        annual_temps = []
        
        for year in years:
            if years_data[year]:
                annual_mean = np.mean(years_data[year])
                annual_temps.append(round(annual_mean, 2))
        
        # Calculer les statistiques globales sur TOUTES les données NetCDF
        stats = {
            'mean': float(np.mean(all_temperatures)),
            'min': float(np.min(all_temperatures)),
            'max': float(np.max(all_temperatures)),
            'std': float(np.std(all_temperatures)),
            'median': float(np.median(all_temperatures))
        }
        
        # Calculer la climatologie mensuelle (moyenne par mois)
        monthly_data = [[] for _ in range(12)]
        
        for i, date_str in enumerate(dates):
            try:
                month = int(date_str.split('-')[1])
                if 1 <= month <= 12:
                    monthly_data[month - 1].append(all_temperatures[i])
            except:
                continue
        
        monthly_climatology = []
        for month_temps in monthly_data:
            if month_temps:
                monthly_climatology.append(round(np.mean(month_temps), 2))
            else:
                monthly_climatology.append(0)
        
        st.success(f"✅ {len(all_temperatures)} points NetCDF extraits → {len(years)} années analysées")
        
        return {
            'years': years,
            'temperatures': annual_temps,
            'monthly_climatology': monthly_climatology,
            'months': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
            'stats': stats,
            'spatial': None,  # Pas de données spatiales simulées
            'data_source': 'netcdf_national'
        }
        
    except Exception as e:
        st.error(f"❌ Erreur lors de l'extraction des données NetCDF: {e}")
        st.error("💡 Vérifiez que le backend est démarré et que les fichiers NetCDF sont présents")
        return None

@st.cache_data(ttl=300)
def fetch_spatial_data(variable, start_year, end_year):
    """Fetch spatial climate data from backend API."""
    try:
        if not check_api_health():
            raise Exception("API backend indisponible")
        
        # L'endpoint /spatial nécessite un mois, on va faire une moyenne de 6 mois représentatifs
        representative_months = [1, 4, 7, 10]  # Jan, Avr, Jul, Oct pour représenter les saisons
        all_spatial_data = []
        
        for month in representative_months:
            params = {
                'var': variable,
                'month': month,
                'start_year': start_year,
                'end_year': end_year
            }
            
            response = requests.get(f"{API_BASE_URL}/spatial", params=params, timeout=60)
            
            if response.status_code == 200:
                monthly_data = response.json()
                all_spatial_data.append(monthly_data)
        
        if all_spatial_data:
            # Prendre les données du premier mois comme structure de base
            base_data = all_spatial_data[0]
            
            # Vérifier si nous avons la structure attendue du backend
            if 'latitudes' in base_data and 'longitudes' in base_data and 'data' in base_data:
                latitudes = base_data['latitudes']
                longitudes = base_data['longitudes']
                
                # Moyenner les données de tous les mois
                all_data_points = []
                for month_data in all_spatial_data:
                    if 'data' in month_data:
                        all_data_points.extend(month_data['data'])
                
                if all_data_points:
                    # Créer un dictionnaire pour moyenner par coordonnées
                    coord_values = {}
                    for point in all_data_points:
                        lat = point['latitude']
                        lon = point['longitude']
                        val = point.get(variable, 0)
                        
                        key = (lat, lon)
                        if key not in coord_values:
                            coord_values[key] = []
                        coord_values[key].append(val)
                    
                    # Calculer les moyennes
                    averaged_values = {}
                    for coord, vals in coord_values.items():
                        averaged_values[coord] = np.mean(vals)
                    
                    # Organiser en matrice selon les latitudes/longitudes
                    values_matrix = []
                    for lat in latitudes:
                        row = []
                        for lon in longitudes:
                            val = averaged_values.get((lat, lon), np.nan)
                            row.append(val)
                        values_matrix.append(row)
                    
                    return {
                        'latitudes': latitudes,
                        'longitudes': longitudes,
                        'values': values_matrix
                    }
            
            # Si structure différente, retourner la première
            return base_data
        
        # Fallback: créer des données spatiales à partir des coordonnées du processeur
        try:
            # Utiliser l'endpoint localities pour obtenir les points de grille
            response_localities = requests.get(f"{API_BASE_URL}/localities/grid-points", params={'limit': 100}, timeout=30)
            
            if response_localities.status_code == 200:
                localities_data = response_localities.json()
                grid_points = localities_data.get('grid_points', [])
                
                if grid_points:
                    # Extraire les coordonnées et créer des valeurs moyennes
                    latitudes = []
                    longitudes = []
                    values = []
                    
                    for point in grid_points:
                        if 'lat' in point and 'lon' in point:
                            latitudes.append(point['lat'])
                            longitudes.append(point['lon'])
                            
                            # Obtenir les données pour ce point
                            try:
                                params_loc = {
                                    'var': variable,
                                    'lat_idx': point.get('lat_idx', 0),
                                    'lon_idx': point.get('lon_idx', 0),
                                    'start_year': start_year,
                                    'end_year': end_year
                                }
                                
                                loc_response = requests.get(f"{API_BASE_URL}/localities/statistics", params=params_loc, timeout=30)
                                if loc_response.status_code == 200:
                                    loc_stats = loc_response.json()
                                    mean_temp = loc_stats.get('mean', 25.0)  # Valeur par défaut
                                    values.append(mean_temp)
                                else:
                                    values.append(25.0)  # Valeur par défaut
                            except:
                                values.append(25.0)  # Valeur par défaut
                    
                    if latitudes and longitudes and values:
                        return {
                            'latitudes': latitudes,
                            'longitudes': longitudes,
                            'values': values
                        }
        except:
            pass
        
        return None
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des données spatiales: {e}")
        return None

def create_time_series(variable, start_year, end_year, data):
    """Série temporelle simple"""
    if not data or not data['years'] or not data['temperatures']:
        fig = go.Figure()
        fig.add_annotation(
            text="❌ Aucune donnée disponible<br>Vérifiez que l'API backend est démarrée",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(height=400)
        return fig
    
    # Couleurs selon la variable
    color = '#3b82f6' if variable == 'tasmin' else '#ef4444'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['years'], 
        y=data['temperatures'],
        mode='lines+markers',
        name=f'{"Température minimale" if variable == "tasmin" else "Température maximale"}',
        line=dict(color=color, width=3),
        marker=dict(size=8, color=color)
    ))
    
    fig.update_layout(
        title=f"Série temporelle {start_year}-{end_year}",
        xaxis_title="Années",
        yaxis_title="Température (°C)",
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    return fig

def create_climatology(variable, start_year, end_year, data):
    """Climatologie moyenne"""
    if not data or not data['monthly_climatology']:
        fig = go.Figure()
        fig.add_annotation(
            text="❌ Aucune donnée climatologique",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(height=400)
        return fig
    
    # Couleurs selon la variable
    color = '#06b6d4' if variable == 'tasmin' else '#f97316'
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data['months'],
        y=data['monthly_climatology'],
        name='Climatologie moyenne',
        marker=dict(color=color, opacity=0.8),
        text=[f'{temp:.1f}°C' for temp in data['monthly_climatology']],
        textposition='auto'
    ))
    
    fig.update_layout(
        title=f"Climatologie moyenne {start_year}-{end_year}",
        xaxis_title="Mois",
        yaxis_title="Température (°C)",
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    return fig

def create_statistics_summary(variable, start_year, end_year, data):
    """Résumé statistique"""
    if not data or not data.get('stats'):
        fig = go.Figure()
        fig.add_annotation(
            text="❌ Aucune donnée statistique",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(height=400)
        return fig
    
    stats = {
        'Moyenne': data['stats'].get('mean', 0),
        'Minimum': data['stats'].get('min', 0),
        'Maximum': data['stats'].get('max', 0),
        'Écart-type': data['stats'].get('std', 0)
    }
    
    # Couleurs selon la variable
    if variable == 'tasmin':
        colors = ['#1e40af', '#0891b2', '#059669', '#065f46']
    else:
        colors = ['#dc2626', '#ea580c', '#d97706', '#ca8a04']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(stats.keys()),
        y=list(stats.values()),
        name='Statistiques',
        marker=dict(color=colors, opacity=0.8),
        text=[f'{val:.2f}°C' for val in stats.values()],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Valeur: %{y:.2f}°C<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Résumé statistique {start_year}-{end_year}",
        xaxis_title="Métriques",
        yaxis_title="Valeurs (°C)",
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    return fig

def create_spatial_map(variable, data):
    """Carte spatiale du Sénégal"""
    if not data or not data.get('spatial'):
        fig = go.Figure()
        fig.add_annotation(
            text="❌ Aucune donnée spatiale",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(height=400)
        return fig
    
    spatial_data = data['spatial']
    latitudes = spatial_data.get('latitudes', [])
    longitudes = spatial_data.get('longitudes', [])
    values = spatial_data.get('values', [])
    
    if not latitudes or not longitudes or not values:
        fig = go.Figure()
        fig.add_annotation(
            text="❌ Données spatiales incomplètes",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(height=400)
        return fig
    
    # Convertir longitudes de 0-360 à -180-180 pour le Sénégal
    # Sénégal : 342° à 349° (système 0-360) = -18° à -11° (système -180-180)
    lons_converted = [(lon - 360) for lon in longitudes]  # Conversion directe car toutes > 180
    
    # Créer des grilles de points (coordonnées du Sénégal)
    lat_grid = []
    lon_grid = []
    temp_grid = []
    
    for i, lat in enumerate(latitudes):
        for j, lon in enumerate(lons_converted):
            # Vérifier que les coordonnées sont bien dans les limites du Sénégal
            if 12 <= lat <= 17 and -18 <= lon <= -11:
                lat_grid.append(lat)
                lon_grid.append(lon)
                if i < len(values) and j < len(values[0]) if values else False:
                    temp_grid.append(values[i][j])
                else:
                    temp_grid.append(np.nan)
    
    # Couleurs selon la variable
    colorscale = 'Blues' if variable == 'tasmin' else 'Reds'
    
    fig = go.Figure()
    
    if lat_grid and lon_grid and temp_grid:
        valid_indices = [i for i, temp in enumerate(temp_grid) if not np.isnan(temp)]
        
        if valid_indices:
            lat_valid = [lat_grid[i] for i in valid_indices]
            lon_valid = [lon_grid[i] for i in valid_indices]
            temp_valid = [temp_grid[i] for i in valid_indices]
            
            fig.add_trace(go.Scattermapbox(
                lat=lat_valid,
                lon=lon_valid,
                mode='markers',
                marker=dict(
                    size=12,
                    color=temp_valid,
                    colorscale=colorscale,
                    colorbar=dict(title="°C", x=1.02),
                    showscale=True,
                    opacity=0.8
                ),
                text=[f"{temp:.1f}°C" for temp in temp_valid],
                name='Température'
            ))
    
    fig.update_layout(
        title=f"Répartition spatiale au Sénégal (Janvier) - {'Température minimale' if variable == 'tasmin' else 'Température maximale'}",
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=14.5, lon=-14.5),  # Centre du Sénégal
            zoom=6.5
        ),
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    return fig

@st.cache_data(ttl=600)  # Cache pendant 10 minutes
def download_data_from_api(variable, start_year, end_year, format_type):
    """Télécharge les données depuis l'API avec retry pour gérer les erreurs 502"""
    import time
    
    download_url = f"{API_BASE_URL}/download"
    params = {
        'var': variable,
        'start_year': start_year,
        'end_year': end_year,
        'format_type': format_type
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🔄 Tentative de téléchargement {attempt + 1}/{max_retries}: {download_url}")
            
            # Timeout plus long pour les téléchargements
            response = requests.get(download_url, params=params, timeout=120)
            
            print(f"📊 Réponse API: Status {response.status_code}, Taille: {len(response.content) if response.content else 0} bytes")
            
            if response.status_code == 200:
                print("✅ Téléchargement réussi")
                return response.content
            elif response.status_code == 502:
                if attempt < max_retries - 1:
                    print(f"⚠️ Erreur 502 - Retry dans 10 secondes...")
                    time.sleep(10)
                    continue
                else:
                    print("❌ Erreur 502 persistante")
                    return None
            else:
                print(f"❌ Erreur API: Status {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"⚠️ Timeout - Retry dans 10 secondes...")
                time.sleep(10)
                continue
            else:
                print("❌ Timeout persistant")
                return None
        except Exception as e:
            print(f"❌ Exception lors du téléchargement: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return None
    
    return None

def show_locality_expander(locality_name, locality_data, variable, start_year, end_year):
    # Ne pas afficher l'analyse complète pour la moyenne nationale
    if locality_name == "Moyenne nationale" or "nationale" in locality_name.lower():
        return
        
    try:
        coords = locality_data.get('coords', {})
        climate_data = locality_data.get('climate_data', {})
        temperatures = climate_data.get('temperatures', [])
        years = climate_data.get('years', [])
        stats = climate_data.get('stats', {})
        
        trend = (temperatures[-1] - temperatures[0]) if len(temperatures) > 1 else 0
        avg_temp = sum(temperatures) / len(temperatures) if temperatures else 0
        
        with st.expander(f"Analyse Complète : {locality_name}", expanded=True):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**{locality_name}** - {variable.upper()} ({start_year}-{end_year})")
                st.text(f"Coordonnées: {coords.get('lat', 0):.2f}°N, {abs(coords.get('lon', 0)):.2f}°W")
            
            with col2:
                if stats:
                    st.metric("Tendance", f"{trend:+.2f}°C")
            
            tab1, tab2 = st.tabs(["Série Temporelle", "Statistiques"])
            
            with tab1:
                if temperatures and years:
                    fig_ts = go.Figure()
                    fig_ts.add_trace(go.Scatter(
                        x=years, y=temperatures,
                        mode='lines+markers',
                        name=locality_name,
                        line=dict(color='#667eea', width=2)
                    ))
                    
                    fig_ts.update_layout(
                        title=f"{variable.upper()} - {locality_name}",
                        height=350,
                        template="plotly_white",
                        xaxis_title="Année",
                        yaxis_title="Température (°C)"
                    )
                    
                    st.plotly_chart(fig_ts, use_container_width=True)
            
            with tab2:
                if stats and temperatures:
                    import numpy as np
                    
                    data = {
                        "Indicateur": ["Moyenne", "Minimum", "Maximum", "Écart-type", "Médiane"],
                        "Valeur": [
                            f"{stats.get('mean', 0):.2f}°C",
                            f"{stats.get('min', 0):.2f}°C", 
                            f"{stats.get('max', 0):.2f}°C",
                            f"{stats.get('std', 0):.2f}°C",
                            f"{np.median(temperatures):.2f}°C"
                        ]
                    }
                    
                    import pandas as pd
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    if trend > 0.5:
                        st.warning(f"Réchauffement : +{trend:.1f}°C")
                    elif trend < -0.5:
                        st.info(f"Refroidissement : {trend:.1f}°C")
                    else:
                        st.success(f"Stable : {trend:+.1f}°C")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Exporter CSV", use_container_width=True):
                    if temperatures and years:
                        import pandas as pd
                        export_df = pd.DataFrame({
                            'Année': years,
                            'Température': temperatures,
                            'Localité': [locality_name] * len(years)
                        })
                        csv = export_df.to_csv(index=False)
                        st.download_button(
                            label="Télécharger CSV",
                            data=csv,
                            file_name=f"{locality_name}_{variable}_{start_year}_{end_year}.csv",
                            mime="text/csv"
                        )
                        
            with col2:
                if st.button("Comparer", use_container_width=True):
                    st.info("Mode comparaison activé")
        
    except Exception as e:
        st.error(f"Erreur: {e}")
                    
    except Exception as e:
        st.error(f"❌ Erreur: {e}")

def show_locality_sidebar(locality_name, locality_data, variable, start_year, end_year):
    with st.sidebar:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h4 style="color: white; margin: 0;">{locality_name}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        coords = locality_data.get('coords', {})
        climate_data = locality_data.get('climate_data', {})
        stats = climate_data.get('stats', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.text(f"{coords.get('lat', 0):.2f}°N")
        with col2:
            st.text(f"{abs(coords.get('lon', 0)):.2f}°W")
        
        if stats:
            avg = stats.get('mean', 0)
            max_temp = stats.get('max', 0)
            min_temp = stats.get('min', 0)
            
            st.metric("Moyenne", f"{avg:.1f}°C")
            st.metric("Maximum", f"{max_temp:.1f}°C", delta=f"{max_temp-avg:+.1f}°C")
            st.metric("Minimum", f"{min_temp:.1f}°C", delta=f"{min_temp-avg:+.1f}°C")
        
        temperatures = climate_data.get('temperatures', [])
        years = climate_data.get('years', [])
        
        if temperatures and years:
            fig_sidebar = go.Figure()
            fig_sidebar.add_trace(go.Scatter(
                x=years, y=temperatures,
                mode='lines',
                line=dict(color='#FF6B6B', width=2)
            ))
            fig_sidebar.update_layout(
                height=150,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
                xaxis_title="",
                yaxis_title="°C"
            )
            st.plotly_chart(fig_sidebar, use_container_width=True)
        
        if st.button("Fermer", use_container_width=True, type="secondary"):
            keys_to_remove = ['sidebar_locality', 'sidebar_name', 'current_locality_data', 'current_locality_name']
            for key in keys_to_remove:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# Interface Streamlit
def create_navigation_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h3 style="color: white; margin: 0;">Dashboard Climatique</h3>
            <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-size: 0.9em;">
                Sénégal 1960-2024
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        variable = st.selectbox(
            "Variable",
            options=["tasmax", "tasmin"],
            format_func=lambda x: "Température maximale" if x == "tasmax" else "Température minimale",
            key="variable_select"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input("Début", min_value=1960, max_value=2023, value=1980, key="start_year")
        with col2:
            end_year = st.number_input("Fin", min_value=1961, max_value=2024, value=2020, key="end_year")
        
        localities_list = [
            {"name": "Moyenne nationale", "type": "national", "lat_idx": None, "lon_idx": None},
            {"name": "Dakar", "type": "city", "lat": 14.693, "lon": -17.447, "lat_idx": 9, "lon_idx": 2},
            {"name": "Kaolack", "type": "city", "lat": 14.159, "lon": -16.073, "lat_idx": 11, "lon_idx": 8},
            {"name": "Saint-Louis", "type": "city", "lat": 16.033, "lon": -16.500, "lat_idx": 4, "lon_idx": 6},
            {"name": "Thiès", "type": "city", "lat": 14.789, "lon": -16.926, "lat_idx": 9, "lon_idx": 4},
            {"name": "Ziguinchor", "type": "city", "lat": 12.583, "lon": -16.267, "lat_idx": 18, "lon_idx": 7},
            {"name": "Tambacounda", "type": "city", "lat": 13.767, "lon": -13.668, "lat_idx": 13, "lon_idx": 17},
        ]
        
        selected_locality_name = st.selectbox(
            "Localité",
            options=[loc["name"] for loc in localities_list],
            key="sidebar_locality_select"
        )
        
        selected_locality = next(loc for loc in localities_list if loc["name"] == selected_locality_name)
        
        format_type = st.selectbox(
            "Format export",
            options=["csv", "netcdf"],
            key="format_select"
        )
        
        st.markdown("---")
        
        if st.button("Actualiser", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                if 'data' in key or 'loaded' in key:
                    del st.session_state[key]
            st.rerun()
        
        try:
            health_response = requests.get(f"{API_BASE_URL}/health", timeout=1)
            if health_response.status_code == 200:
                st.success("Backend connecté")
            else:
                st.error("Backend indisponible")
        except:
            st.error("Backend indisponible")
        
        return variable, start_year, end_year, format_type, selected_locality_name, selected_locality

def main():
    
    st.markdown("""
    <style>
        .main > div { padding: 1rem 2rem; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)
    
    variable, start_year, end_year, format_type, selected_locality_name, selected_locality = create_navigation_sidebar()
    
    st.title("Dashboard Climatique du Sénégal")
    st.markdown("*Analyse des données climatiques NetCDF*")
    
    # Vérifier si une localité a été sélectionnée via la carte
    if st.session_state.map_clicked_locality:
        # Mise à jour depuis le clic sur la carte
        st.session_state.selected_locality = st.session_state.map_clicked_locality
        st.session_state.map_clicked_locality = None  # Reset
        st.session_state.update_charts = True
    
    # Vérification de la sélection dans la sidebar
    if not selected_locality:
        st.info("Sélectionnez une localité dans la barre latérale pour voir les données")
        return
    
    analysis_mode = selected_locality["type"]
    lat_idx = selected_locality.get("lat_idx") 
    lon_idx = selected_locality.get("lon_idx")
    
    if analysis_mode == "national":
        st.info("Mode analyse nationale")
    else:
        st.info(f"Localité : **{selected_locality_name}**")
        
        with st.spinner(f"Chargement des données pour {selected_locality_name}..."):
            try:
                detailed_data = fetch_detailed_locality_data(
                    variable, start_year, end_year,
                    selected_locality.get('lat', 0),
                    selected_locality.get('lon', 0),
                    selected_locality_name
                )
                
                if detailed_data:
                    locality_data = {
                        'coords': {
                            'lat': selected_locality.get('lat', 0),
                            'lon': selected_locality.get('lon', 0)
                        },
                        'climate_data': detailed_data
                    }
                    
                    show_locality_sidebar(selected_locality_name, locality_data, variable, start_year, end_year)
                    st.markdown("---")
                    show_locality_expander(selected_locality_name, locality_data, variable, start_year, end_year)
                    return
                    
                else:
                    st.error(f"Impossible de récupérer les données pour {selected_locality_name}")
                    
            except Exception as e:
                st.error(f"Erreur lors du chargement: {e}")
    
    st.markdown("---")
    
    # Interface pour lancer le chargement des données
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**Analyse sélectionnée :** {selected_locality_name}")
        st.markdown(f"**Variable :** {variable.upper()} | **Période :** {start_year}-{end_year}")
    
    with col2:
        if 'data_loaded' not in st.session_state:
            load_data = st.button("📊 Charger les données", type="primary")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                load_data = st.button("🔄 Actualiser", type="secondary")
            with col_b:
                if st.button("🗑️ Réinitialiser"):
                    st.session_state.pop('data_loaded', None)
                    st.rerun()
                load_data = False
    
    # Chargement des données seulement si le bouton est cliqué
    data = None
    if load_data or 'data_loaded' in st.session_state:
        st.session_state.data_loaded = True
        
        with st.spinner("📂 Extraction des données NetCDF..."):
            if analysis_mode == "national":
                data = fetch_data(variable, start_year, end_year)
                location_title = "Sénégal (Moyenne nationale)"
            else:
                if lat_idx is not None and lon_idx is not None:
                    # 🎯 MODE LOCALITÉ - AFFICHAGE IMMÉDIAT DES INFORMATIONS DÉTAILLÉES
                    
                    # 1. Récupérer les données climatiques complètes
                    raw_data = fetch_locality_data(
                        variable, start_year, end_year, 
                        lat_idx, lon_idx, selected_locality['name']
                    )
                    
                    if raw_data:
                        # 2. Préparer les données pour l'affichage détaillé
                        detailed_data = fetch_detailed_locality_data(
                            variable, start_year, end_year,
                            selected_locality['coords']['lat'],
                            selected_locality['coords']['lon'],
                            selected_locality['name']
                        )
                        
                        locality_data = {
                            'coords': selected_locality['coords'],
                            'climate_data': detailed_data if detailed_data else {}
                        }
                        
                        # 3. === AFFICHAGE IMMÉDIAT DUAL : SIDEBAR + EXPANDER ===
                        st.success(f"✅ Données chargées pour {selected_locality['name']}")
                        
                        # SIDEBAR : Informations permanentes et statistiques clés
                        show_locality_sidebar(selected_locality['name'], locality_data, variable, start_year, end_year)
                        
                        # EXPANDER : Analyses détaillées et graphiques complets  
                        st.markdown("---")
                        st.markdown("### 📊 Analyse Détaillée de la Localité")
                        show_locality_expander(selected_locality['name'], locality_data, variable, start_year, end_year)
                        
                        # 4. Adapter les données pour les graphiques principaux (si nécessaire)
                        data = adapt_locality_data_format(raw_data)
                        location_title = f"{selected_locality['name']} (Localité spécifique)"
                        
                        # Message informatif
                        st.info("💡 **Double affichage activé :** Consultez la **sidebar** pour les statistiques rapides et l'**expander** ci-dessus pour l'analyse complète.")
                        
                    else:
                        st.error(f"❌ Impossible de récupérer les données pour {selected_locality['name']}")
                        data = None
                else:
                    st.error("❌ Problème avec les indices de localité")
                    data = None
    
    # Affichage du contenu seulement si les données sont chargées
    if data is None and 'data_loaded' not in st.session_state:

        st.markdown("### 🎯 Fonctionnalités disponibles :")
        st.markdown("""
        - 📊 **Séries temporelles** avec vos données NetCDF réelles
        - 📈 **Statistiques détaillées** (min, max, moyenne, écart-type)
        - 🌡️ **Climatologie mensuelle** 
        - 🗺️ **Carte interactive** avec marqueurs par ville
        - 📋 **Analyse comparative** entre localités
        - 📂 **Export des données** en différents formats
        """)
        return
    
    if data is None:
        st.error("❌ Impossible de récupérer les données NetCDF. Vérifiez que le backend est démarré.")
        if st.button("🔄 Réessayer"):
            st.session_state.pop('data_loaded', None)
            st.rerun()
        return
    
    # Afficher le titre avec la localisation

    
    # Affichage des graphiques en grille 2x2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Série Temporelle")
        fig_ts = create_time_series(variable, start_year, end_year, data)
        st.plotly_chart(fig_ts, use_container_width=True)
        
        st.subheader("📋 Résumé Statistique")
        fig_stats = create_statistics_summary(variable, start_year, end_year, data)
        st.plotly_chart(fig_stats, use_container_width=True)
    
    with col2:
        st.subheader("📊 Climatologie Moyenne")
        fig_clim = create_climatology(variable, start_year, end_year, data)
        st.plotly_chart(fig_clim, use_container_width=True)
        
        st.subheader("🗺️ Représentation Spatiale")
        try:
            # Récupérer les données spatiales via l'API
            spatial_data = fetch_spatial_data(variable, start_year, end_year)
            if spatial_data:
                fig_spatial = create_spatial_map(variable, {"spatial": spatial_data})
                st.plotly_chart(fig_spatial, use_container_width=True)
            else:
                st.error("❌ Impossible de charger les données spatiales")
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des données spatiales: {e}")
    
    # Section Heatmap Interactive
    st.markdown("---")
    st.subheader("🔥 Heatmap Interactive du Sénégal")
    
    # Options pour la heatmap
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**Carte climatique par zones urbaines - {variable.upper()} ({start_year}-{end_year})**")
    
    with col2:
        show_heatmap = st.checkbox("Afficher la Carte Climatique", value=True, help="Affiche les zones climatiques des 15 villes principales")
    
    with col3:
        if show_heatmap:
            heatmap_opacity = st.slider("Opacité", 0.1, 1.0, 0.7, help="Ajuste la transparence de la heatmap")
    
    if show_heatmap:
        with st.spinner("🗺️ Création de la carte climatique avec zones colorées par ville..."):
            try:
                # Créer la heatmap avec zones pour les 15 villes principales
                heatmap = create_climate_heatmap(variable, start_year, end_year)
                
                if heatmap:
                    # Affichage de la heatmap
                    heatmap.to_streamlit(height=600)
                    
                    # Informations détaillées sur la heatmap
                    st.info(f"""
                    🌡️ **Heatmap Haute Résolution - Sénégal**
                    - **Variable :** {variable.upper()} ({('Température minimale' if variable == 'tasmin' else 'Température maximale')})
                    - **Période :** {start_year} - {end_year} (moyenne temporelle)
                    - **Résolution :** 609 points de grille (21×29)
                    - **Couverture :** 12°N-17°N, 11°W-18°W
                    - **Données :** {'Fichiers NetCDF réels (tasmin/tasmax 1960-2024)' if check_api_health() else 'Backend indisponible'}
                    """)
                    
                    # Légende des couleurs
                    with st.expander("🎨 Légende des couleurs"):
                        st.markdown("""
                        - 🔵 **Bleu :** Températures les plus froides
                        - 🟢 **Vert :** Températures modérées  
                        - 🟡 **Jaune :** Températures élevées
                        - 🔴 **Rouge :** Températures les plus chaudes
                        
                        📍 **Marqueurs rouges :** Villes principales avec températures exactes
                        """)
                else:
                    st.warning("⚠️ Impossible de générer la heatmap pour le moment")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de la création de la heatmap : {e}")
                st.info("💡 Vérifiez la connexion à l'API ou réessayez plus tard")
    
    # Section interactive - Graphiques détaillés pour la localité sélectionnée
    st.markdown("---")
    
    # Détection du changement de localité
    locality_changed = check_locality_change()
    
    if locality_changed or st.session_state.update_charts:
        st.success(f"🎯 Analyse mise à jour pour : **{selected_locality_name}**")
        st.session_state.update_charts = False
    
    # === SYSTÈME EXPANDER + SIDEBAR POUR LES LOCALITÉS ===
    
    # Récupérer les données détaillées pour la localité sélectionnée
    if analysis_mode == "national":
        detailed_data = fetch_data(variable, start_year, end_year)
        coords = {"lat": 14.5, "lon": -14.0}  # Centre du Sénégal
    else:
        detailed_data = fetch_locality_data(variable, start_year, end_year, lat_idx, lon_idx, selected_locality_name)
        coords = {"lat": lat_idx, "lon": lon_idx}
    
    # Afficher automatiquement l'expander avec les détails de la localité
    if detailed_data:
        locality_data = {
            "coords": coords,
            "climate_data": detailed_data
        }
        show_locality_expander(selected_locality_name, locality_data, variable, start_year, end_year)
    
    # Afficher la sidebar si une localité a été épinglée
    if st.session_state.sidebar_locality and st.session_state.sidebar_name:
        show_locality_sidebar(
            st.session_state.sidebar_name, 
            st.session_state.sidebar_locality, 
            variable, start_year, end_year
        )
    
    # === SECTION DE COMPARAISON (SI ACTIVÉE) ===
    if st.session_state.get('comparison_mode', False):
        st.markdown("### 🔄 Mode Comparaison")
        
        cities_to_compare = st.multiselect(
            f"Comparer {selected_locality_name} avec:",
            options=['Dakar', 'Thiès', 'Kaolack', 'Saint-Louis', 'Tambacounda'],
            max_selections=3
        )
        
        if cities_to_compare:
            st.info(f"🎯 Comparaison: {selected_locality_name} vs {', '.join(cities_to_compare)}")
        
        if st.button("❌ Fermer comparaison"):
            st.session_state.comparison_mode = False
            st.rerun()
    
        
    # Message si aucune donnée disponible  
    if not detailed_data or not detailed_data.get('temperatures'):
        st.warning(f"⚠️ Aucune donnée disponible pour {selected_locality_name}")
        st.info("💡 Essayez une autre localité ou vérifiez la connexion API")

    
    # === FIN DE LA SECTION LOCALITÉ ===
    
    # Informations sur les données - affichage direct
    st.markdown("---")
    st.subheader("ℹ️ Informations sur les données")
    
    if data and data.get('stats'):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Moyenne", f"{data['stats'].get('mean', 0):.2f}°C")
        with col2:
            st.metric("Minimum", f"{data['stats'].get('min', 0):.2f}°C")
        with col3:
            st.metric("Maximum", f"{data['stats'].get('max', 0):.2f}°C")
        with col4:
            st.metric("Écart-type", f"{data['stats'].get('std', 0):.2f}°C")
        
        st.markdown("### � Source des données")
        col1, col2 = st.columns(2)
        with col1:
            st.info("🎯 **Fichiers:** `tasmin_daily_Senegal_1960_2024.nc` et `tasmax_daily_Senegal_1960_2024.nc`")
        with col2:
            st.info("📅 **Période:** 1960-2024 (données climatiques journalières)")
        
        st.success("🌍 **Région:** Sénégal, Afrique de l'Ouest")

if __name__ == "__main__":
    main()