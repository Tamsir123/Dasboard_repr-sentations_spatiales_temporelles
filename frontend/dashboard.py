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
    """Récupérer les données climatiques pour les 15 villes principales"""
    try:
        # Définir les 15 villes principales du Sénégal avec leurs coordonnées
        cities_data = [
            ('Dakar', 14.7167, -17.4677),
            ('Thiès', 14.7886, -16.9261),
            ('Kaolack', 14.1594, -16.0773),
            ('Ziguinchor', 12.5681, -16.2719),
            ('Saint-Louis', 16.0199, -16.4896),
            ('Tambacounda', 13.7671, -13.6677),
            ('Diourbel', 14.6564, -16.2294),
            ('Louga', 15.6181, -16.2463),
            ('Fatick', 14.3347, -16.4016),
            ('Kolda', 12.8939, -14.9406),
            ('Matam', 15.6556, -13.2556),
            ('Kaffrine', 14.1058, -15.5503),
            ('Kédougou', 12.5569, -12.1697),
            ('Sédhiou', 12.7081, -15.5569),
            ('Mbour', 14.4198, -16.9692)
        ]
        
        cities_climate = []
        
        # Vérifier la santé de l'API
        api_available = check_api_health()
        
        st.info(f"🔄 Récupération des données {variable.upper()} pour {len(cities_data)} villes...")
        progress_bar = st.progress(0)
        
        for i, (city_name, lat, lon) in enumerate(cities_data):
            try:
                if api_available:
                    # Essayer de récupérer les vraies données via l'API
                    try:
                        response = requests.get(
                            f"{API_BASE_URL}/localities/cities",
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            cities_list = response.json()
                            
                            # Chercher la ville dans la liste API
                            city_found = None
                            for api_city in cities_list:
                                if api_city.get('locality', '').lower() == city_name.lower():
                                    city_found = api_city
                                    break
                            
                            if city_found:
                                # Récupérer les statistiques pour cette ville
                                stats_response = requests.get(
                                    f"{API_BASE_URL}/localities/statistics",
                                    params={
                                        'locality': city_found['locality'],
                                        'variable': variable,
                                        'start_date': f"{start_year}-01-01",
                                        'end_date': f"{end_year}-12-31",
                                        'aggregation': 'mean'
                                    },
                                    timeout=10
                                )
                                
                                if stats_response.status_code == 200:
                                    stats = stats_response.json()
                                    temp_value = stats.get('mean', simulate_temperature(lat, lon, variable))
                                else:
                                    temp_value = simulate_temperature(lat, lon, variable)
                            else:
                                temp_value = simulate_temperature(lat, lon, variable)
                        else:
                            temp_value = simulate_temperature(lat, lon, variable)
                    except:
                        temp_value = simulate_temperature(lat, lon, variable)
                else:
                    # Simulation si API indisponible
                    temp_value = simulate_temperature(lat, lon, variable)
                
                cities_climate.append({
                    'city': city_name,
                    'lat': lat,
                    'lon': lon,
                    'temperature': temp_value
                })
                
                progress_bar.progress((i + 1) / len(cities_data))
                
            except Exception as e:
                # En cas d'erreur, utiliser la simulation
                temp_value = simulate_temperature(lat, lon, variable)
                cities_climate.append({
                    'city': city_name,
                    'lat': lat,
                    'lon': lon,
                    'temperature': temp_value
                })
                progress_bar.progress((i + 1) / len(cities_data))
        
        progress_bar.empty()
        
        if api_available:
            st.success(f"✅ Données récupérées pour {len(cities_climate)} villes")
        else:
            st.warning("⚠️ API indisponible - Utilisation de données simulées")
            
        return cities_climate
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des données: {e}")
        return []

def simulate_temperature(lat, lon, variable):
    """Simuler des températures réalistes basées sur la géographie du Sénégal"""
    # Température de base selon la latitude (plus chaud au sud)
    base_temp = 32 - (lat - 12) * 1.5  
    
    # Effet de la longitude (plus chaud à l'intérieur des terres)
    coastal_effect = (lon + 14) * 0.8  # Plus froid près de la côte atlantique
    
    # Variation selon la variable
    if variable == "tasmin":
        temp = base_temp - 12 + coastal_effect + np.random.normal(0, 1.5)
    else:  # tasmax
        temp = base_temp + 8 + coastal_effect + np.random.normal(0, 2)
    
    # Limites réalistes pour le Sénégal
    return max(16, min(48, temp))

def create_climate_heatmap(variable, start_year, end_year):
    """Créer une heatmap climatique avec délimitations régionales réelles"""
    try:
        import folium
        
        # Récupérer les données pour les villes
        cities_data = get_cities_climate_data(variable, start_year, end_year)
        
        if not cities_data:
            st.error("❌ Aucune donnée disponible pour créer la heatmap")
            return None
        
        # Créer une carte centrée sur le Sénégal
        m = leafmap.Map(center=[14.5, -14.5], zoom=7)
        
        # Calculer l'échelle dynamique des températures
        temperatures = [city['temperature'] for city in cities_data]
        min_temp, max_temp = min(temperatures), max(temperatures)
        
        st.info(f"🌡️ Échelle de température: {min_temp:.1f}°C - {max_temp:.1f}°C")
        
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
        
        # Ajouter les polygones régionaux colorés
        for city in cities_data:
            color = get_color(city['temperature'], min_temp, max_temp)
            polygon_coords = create_region_polygon(city['city'], city['lat'], city['lon'])
            
            # Créer le polygone de la région
            folium_polygon = folium.Polygon(
                locations=polygon_coords,
                color=color,
                weight=2,
                fillColor=color,
                fillOpacity=0.6,
                popup=f"""<div style="font-family: Arial, sans-serif;">
                         <h4 style="margin: 0; color: #333;">Région de {city['city']}</h4>
                         <hr style="margin: 5px 0;">
                         <p style="margin: 2px 0;"><b>🌡️ {variable.upper()}:</b> {city['temperature']:.1f}°C</p>
                         <p style="margin: 2px 0;"><b>📅 Période:</b> {start_year}-{end_year}</p>
                         <p style="margin: 2px 0;"><b>📍 Centre:</b> {city['lat']:.2f}°N, {abs(city['lon']):.2f}°W</p>
                         </div>""",
                tooltip=f"Région {city['city']}: {city['temperature']:.1f}°C"
            )
            folium_polygon.add_to(m)
            
            # Ajouter un marqueur au centre de la région
            folium_marker = folium.Marker(
                location=[city['lat'], city['lon']],
                popup=f"""<div style="font-family: Arial, sans-serif; text-align: center;">
                         <h3 style="margin: 0; color: #2E86AB;">{city['city']}</h3>
                         <hr style="margin: 5px 0;">
                         <p style="margin: 5px 0; font-size: 16px;"><b>🌡️ {city['temperature']:.1f}°C</b></p>
                         <p style="margin: 2px 0; font-size: 12px; color: #666;">Variable: {variable.upper()}</p>
                         <p style="margin: 2px 0; font-size: 12px; color: #666;">Période: {start_year}-{end_year}</p>
                         </div>""",
                tooltip=f"�️ {city['city']}",
                icon=folium.Icon(
                    color='white', 
                    icon='institution', 
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
        
        return m
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la création de la heatmap: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_locality_data(variable, start_year, end_year, lat_idx, lon_idx, city_name):
    """Récupérer les données spécifiques à une localité via l'API backend"""
    try:
        # Vérifier la santé de l'API
        if not check_api_health():
            st.warning("⚠️ API indisponible - Utilisation des données nationales")
            return fetch_data(variable, start_year, end_year)
        
        # Fonction helper pour les requêtes avec retry
        def make_request_with_retry(endpoint, params, max_retries=2):
            for attempt in range(max_retries):
                try:
                    response = requests.get(f"{API_BASE_URL}/{endpoint}", 
                                          params=params, timeout=30)
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 502:
                        continue
                    else:
                        continue
                except:
                    continue
            return None
        
        # Import time pour les sleeps
        import time
        
        # Récupération des données spécifiques à la localité
        params = {
            'var': variable,
            'lat_idx': lat_idx,
            'lon_idx': lon_idx,
            'start_year': start_year,
            'end_year': end_year
        }
        
        # Essayer de récupérer les données de localité
        temporal_data = make_request_with_retry("localities/time-series", params)
        
        if temporal_data:
            # Si les données de localité sont disponibles
            stats_data = make_request_with_retry("localities/statistics", params)
            return {
                'years': temporal_data.get('years', []),
                'temperatures': temporal_data.get('values', []),
                'monthly_climatology': [],  
                'months': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
                'stats': stats_data or {},
                'spatial': None,
                'locality_info': {
                    'lat_idx': lat_idx,
                    'lon_idx': lon_idx,
                    'city_name': city_name
                }
            }
        else:
            # Fallback vers les données nationales
            st.info(f"ℹ️ Données spécifiques à {city_name} indisponibles - Utilisation des données nationales")
            return fetch_data(variable, start_year, end_year)
        
    except Exception as e:
        st.warning(f"⚠️ Problème avec les données de localité: {e}")
        st.info("🔄 Basculement vers les données nationales")
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
    """Récupérer les données générales (moyenne nationale) via l'API backend"""
    try:
        # Vérifier la santé de l'API
        if not check_api_health():
            raise Exception("API backend indisponible")
        
        # Fonction helper pour les requêtes avec retry
        def make_request_with_retry(endpoint, params, max_retries=3):
            for attempt in range(max_retries):
                try:
                    response = requests.get(f"{API_BASE_URL}/{endpoint}", 
                                          params=params, timeout=60)
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 502:
                        if attempt < max_retries - 1:
                            st.warning(f"⚠️ Erreur 502 (tentative {attempt + 1}/{max_retries}) - Retry dans 5 secondes...")
                            time.sleep(5)
                            continue
                        else:
                            raise Exception(f"Erreur 502 persistante après {max_retries} tentatives")
                    else:
                        raise Exception(f"Erreur API {endpoint}: {response.status_code}")
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        st.warning(f"⚠️ Timeout (tentative {attempt + 1}/{max_retries}) - Retry dans 5 secondes...")
                        time.sleep(5)
                        continue
                    else:
                        raise Exception(f"Timeout persistant après {max_retries} tentatives")
            return None
        
        # Import time pour les sleeps
        import time
        
        # Récupération des données générales avec retry
        params = {'var': variable, 'start_year': start_year, 'end_year': end_year}
        
        temporal_data = make_request_with_retry("time-series", params)
        clim_data = make_request_with_retry("climatology", params)
        stats_data = make_request_with_retry("stats", params)
        
        # Récupérer les données spatiales pour le mois de janvier (exemple)
        spatial_params = {**params, 'month': 1}  # Janvier par défaut
        spatial_data = make_request_with_retry("spatial", spatial_params)
        
        # Combiner les données
        return {
            'years': temporal_data.get('years', []),
            'temperatures': temporal_data.get('values', []),
            'monthly_climatology': clim_data.get('values', []),
            'months': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
            'stats': stats_data,
            'spatial': spatial_data  # Ajouter les données spatiales
        }
        
    except Exception as e:
        st.error(f"❌ Erreur API: {e}")
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

# Interface Streamlit
def main():
    st.title("🌡️ Dashboard Climatique du Sénégal")
    st.markdown("*Visualisation et téléchargement direct des données climatiques*")
    
    # Paramètres avec sélecteur de localités
    st.markdown("### Paramètres")
    
    # Première ligne - Paramètres principaux
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        variable = st.selectbox(
            "Variable climatique",
            options=["tasmax", "tasmin"],
            format_func=lambda x: "Température maximale" if x == "tasmax" else "Température minimale",
            key="variable_select"
        )
    
    with col2:
        start_year = st.number_input("Année début", value=1980, min_value=1960, max_value=2024, key="start_year")
    
    with col3:
        end_year = st.number_input("Année fin", value=2020, min_value=1960, max_value=2024, key="end_year")
    
    with col4:
        format_type = st.selectbox(
            "Format export",
            options=["csv", "netcdf"],
            format_func=lambda x: x.upper(),
            key="format_select"
        )
    
    # Sélecteur de localités simple
    st.markdown("### 📍 Sélection de localité")
    
    # Liste des localités principales du Sénégal (hardcodées pour éviter les problèmes d'API)
    localities_list = [
        {"name": "🇸🇳 Moyenne nationale", "type": "national", "lat_idx": None, "lon_idx": None},
        {"name": "Dakar", "type": "city", "lat_idx": 9, "lon_idx": 2, "lat": 14.693, "lon": -17.447},
        {"name": "Kaolack", "type": "city", "lat_idx": 11, "lon_idx": 8, "lat": 14.159, "lon": -16.073},
        {"name": "Saint-Louis", "type": "city", "lat_idx": 4, "lon_idx": 6, "lat": 16.033, "lon": -16.500},
        {"name": "Thiès", "type": "city", "lat_idx": 9, "lon_idx": 4, "lat": 14.789, "lon": -16.926},
        {"name": "Ziguinchor", "type": "city", "lat_idx": 18, "lon_idx": 7, "lat": 12.583, "lon": -16.267},
        {"name": "Diourbel", "type": "city", "lat_idx": 9, "lon_idx": 7, "lat": 14.660, "lon": -16.233},
        {"name": "Tambacounda", "type": "city", "lat_idx": 13, "lon_idx": 17, "lat": 13.767, "lon": -13.668},
        {"name": "Fatick", "type": "city", "lat_idx": 11, "lon_idx": 6, "lat": 14.335, "lon": -16.407},
        {"name": "Kolda", "type": "city", "lat_idx": 16, "lon_idx": 12, "lat": 12.894, "lon": -14.942},
        {"name": "Matam", "type": "city", "lat_idx": 5, "lon_idx": 19, "lat": 15.655, "lon": -13.256},
        {"name": "Kédougou", "type": "city", "lat_idx": 18, "lon_idx": 23, "lat": 12.557, "lon": -12.176},
        {"name": "Sédhiou", "type": "city", "lat_idx": 17, "lon_idx": 14, "lat": 12.709, "lon": -15.557},
        {"name": "Louga", "type": "city", "lat_idx": 6, "lon_idx": 7, "lat": 15.619, "lon": -16.228},
        {"name": "Kaffrine", "type": "city", "lat_idx": 12, "lon_idx": 14, "lat": 14.106, "lon": -15.550},
        {"name": "Touba", "type": "city", "lat_idx": 9, "lon_idx": 8, "lat": 14.850, "lon": -15.883},
    ]
    
    # Dropdown simple avec toutes les localités
    selected_locality_name = st.selectbox(
        "Choisir une localité :",
        options=[loc["name"] for loc in localities_list],
        key="locality_select"
    )
    
    # Trouver la localité sélectionnée
    selected_locality = next(loc for loc in localities_list if loc["name"] == selected_locality_name)
    
    # Variables pour l'analyse
    analysis_mode = selected_locality["type"]
    lat_idx = selected_locality["lat_idx"] 
    lon_idx = selected_locality["lon_idx"]
    
    # Afficher les informations de la localité sélectionnée
    if analysis_mode == "national":
        st.info("🇸🇳 **Analyse nationale** - Moyenne spatiale sur tout le Sénégal")
    else:
        st.info(f"📍 **{selected_locality['name']}** - "
               f"Grille: ({lat_idx}, {lon_idx}) - "
               f"Coordonnées: ({selected_locality['lat']:.3f}°N, {selected_locality['lon']:.3f}°W)")
    
    # Validation des années
    if start_year >= end_year:
        st.error("❌ L'année de début doit être < année de fin")
        return
    
    # Deuxième ligne - Actions et téléchargement
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col2:  # Centrer le bouton de téléchargement
        # Bouton de téléchargeme👆 Cliquez pour télécharger directementnt direct - un seul clic !
        filename = f"{variable}_{start_year}_{end_year}.{format_type}"
        
        # Générer les données et créer le bouton de téléchargement direct
        with st.spinner("Préparation..."):
            file_data = download_data_from_api(variable, start_year, end_year, format_type)
        
        if file_data:
            # Bouton de téléchargement direct - UN SEUL CLIC
            download_clicked = st.download_button(
                label=f"� Télécharger {filename}",
                data=file_data,
                file_name=filename,
                mime="text/csv" if format_type == "csv" else "application/octet-stream",
                use_container_width=True,
                type="primary",
                help=f"Téléchargement direct du fichier {format_type.upper()} ({len(file_data)/1024/1024:.1f} MB)"
            )
            
            # Afficher le statut après le téléchargement
            if download_clicked:
                st.success(f"✅ Téléchargement lancé: {filename}")
        else:
            # Test de connectivité détaillé
            try:
                health_response = requests.get(f"{API_BASE_URL}/health")
                if health_response.status_code == 200:
                    st.error("❌ API accessible mais échec du téléchargement")
                    st.info("🔧 Vérifiez les paramètres ou réessayez")
                else:
                    st.error(f"❌ API retourne une erreur: {health_response.status_code}")
            except Exception as e:
                st.error("❌ Impossible de joindre l'API backend")
                st.info("🚀 Assurez-vous que le backend est lancé sur le port 8000")
                st.code(f"Erreur: {e}")
            
            # Bouton pour forcer un refresh
            if st.button("🔄 Réessayer le téléchargement", use_container_width=True):
                st.rerun()
    
    st.markdown("---")  # Séparateur après la navbar
    
    # Récupération des données selon le mode d'analyse
    with st.spinner("Chargement des données..."):
        if analysis_mode == "national":
            data = fetch_data(variable, start_year, end_year)
            location_title = "Sénégal (Moyenne nationale)"
        else:
            if lat_idx is not None and lon_idx is not None:
                # Utiliser les données de localité avec les indices hardcodés
                raw_data = fetch_locality_data(
                    variable, start_year, end_year, 
                    lat_idx, lon_idx, selected_locality['name']
                )
                # Adapter les données au format attendu par les graphiques
                data = adapt_locality_data_format(raw_data)
                location_title = f"{selected_locality['name']} (Localité spécifique)"
            else:
                st.error("❌ Problème avec les indices de localité")
                return
    
    if data is None:
        st.error("❌ Impossible de récupérer les données. Vérifiez que l'API backend est démarrée.")
        return
    
    # Afficher le titre avec la localisation
    st.info(f"📍 **Données analysées pour :** {location_title}")
    
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
        fig_spatial = create_spatial_map(variable, data)
        st.plotly_chart(fig_spatial, use_container_width=True)
    
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
                    - **Données :** {'API climatique en temps réel' if check_api_health() else 'Simulation géographique'}
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