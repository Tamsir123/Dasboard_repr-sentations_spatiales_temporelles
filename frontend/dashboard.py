import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import json
import tempfile
import os
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

@st.cache_data(ttl=300)
def fetch_data(variable, start_year, end_year):
    """Récupérer les données via l'API backend avec gestion d'erreur améliorée"""
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
        
        # Récupération des données avec retry
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
    
    # Paramètres simples
    st.markdown("### Paramètres")
    
    # Colonnes simples
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        variable = st.selectbox(
            "Variable climatique",
            options=["tasmax", "tasmin"],
            format_func=lambda x: "Température maximale" if x == "tasmax" else "Température minimale",
            key="variable_select"
        )
    
    with col2:
        start_year = st.number_input("Année début", value=1960, min_value=1960, max_value=2024, key="start_year")
    
    with col3:
        end_year = st.number_input("Année fin", value=2024, min_value=1960, max_value=2024, key="end_year")
    
    with col4:
        format_type = st.selectbox(
            "Format export",
            options=["csv", "netcdf"],
            format_func=lambda x: x.upper(),
            key="format_select"
        )
    
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
    
    # Récupération des données
    with st.spinner("Chargement des données..."):
        data = fetch_data(variable, start_year, end_year)
    
    if data is None:
        st.error("❌ Impossible de récupérer les données. Vérifiez que l'API backend est démarrée.")
        return
    
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