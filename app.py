import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import difflib
import math
import requests
import json

# Configuration de la page
st.set_page_config(
    page_title="SunuGuide - Assistant Transport",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# VOTRE CLÉ API INTÉGRÉE
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjQ4YzZhZDMzMTcwOTRmOGFiZmQ3MzI5ZjgxYzcxOGIyIiwiaCI6Im11cm11cjY0In0="

# Classes du modèle
class DataPreprocessor:
    def __init__(self, df):
        self.df = df.copy()
    
    def clean_data(self):
        self.df['rapidite'] = self.df['rapidite'].fillna(5.0)
        self.df['confort'] = self.df['confort'].fillna(5.0)
        return self
    
    def create_features(self):
        self.df['categorie_prix'] = pd.cut(self.df['prix'], 
                                         bins=[0, 500, 2000, 50000],
                                         labels=['Économique', 'Moyen', 'Cher'])
        self.df['score_basique'] = (self.df['rapidite'] + self.df['confort']) / 2
        return self
    
    def get_data(self):
        return self.df

class DistanceCalculator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car"
        self.headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        
        # Coordonnées GPS des stations principales de Dakar
        self.station_coordinates = {
            'parcelles assainies': (14.7677, -17.3980),
            'golf nord': (14.7589, -17.3944),
            'le plateau': (14.6770, -17.4370),
            'grande mosquee': (14.6828, -17.4472),
            'liberte 5': (14.7214, -17.4639),
            'liberte 6': (14.7261, -17.4700),
            'grand medine': (14.6986, -17.4689),
            'prefecture guediawaye': (14.7833, -17.4000),
            'dalal jam': (14.7750, -17.4050),
            'croisement 22': (14.7400, -17.4500),
            'papa gueye fall (petersen)': (14.7150, -17.4550),
            'place de la nation': (14.7050, -17.4580),
            'grand dakar': (14.7100, -17.4450),
            'dakar': (14.6928, -17.4467),
            'hann': (14.7200, -17.4200),
            'colobane': (14.6900, -17.4600),
            'hann maristes': (14.7150, -17.4250),
            'bountou pikine': (14.7500, -17.3900),
            'thiaroye': (14.7600, -17.3700),
            'yeumbeul': (14.7700, -17.3500),
            'rufisque': (14.7150, -17.2800),
            'bargny': (14.7000, -17.2300),
            'diamniadio': (14.7000, -17.2000),
            'yoff': (14.7500, -17.4800),
            'ouakam': (14.7300, -17.4900),
            'mermoz': (14.7000, -17.4700),
            'fann': (14.6800, -17.4700),
            'point e': (14.6900, -17.4650),
            'sacré coeur': (14.7100, -17.4750),
            'medina': (14.6750, -17.4400),
            'gare routière': (14.6800, -17.4350),
            'terminus libert 5': (14.7214, -17.4639),
            'terminus gudiawaye': (14.7833, -17.4000),
            'terminus keur massar': (14.7700, -17.3300),
            'scat urbam': (14.6700, -17.4400),
            'dieuppeul': (14.6850, -17.4550),
            'centre-ville': (14.6770, -17.4370)
        }
    
    def get_station_coordinates(self, station_name):
        """Trouve les coordonnées GPS d'une station"""
        station_lower = station_name.lower()
        
        # Recherche exacte
        for station, coords in self.station_coordinates.items():
            if station in station_lower or station_lower in station:
                return coords
        
        # Recherche partielle
        for station, coords in self.station_coordinates.items():
            if any(word in station_lower for word in station.split()):
                return coords
        
        # Fallback pour Dakar centre
        return (14.6928, -17.4467)
    
    def calculate_real_distance(self, depart, arrivee):
        """Calcule la distance réelle via l'API OpenRouteService"""
        try:
            # Obtenir les coordonnées
            dep_coords = self.get_station_coordinates(depart)
            arr_coords = self.get_station_coordinates(arrivee)
            
            # Préparer la requête API
            body = {
                "coordinates": [
                    [dep_coords[1], dep_coords[0]],  # [longitude, latitude]
                    [arr_coords[1], arr_coords[0]]
                ],
                "instructions": False,
                "preference": "recommended"
            }
            
            # Faire l'appel API
            response = requests.post(
                self.base_url,
                json=body,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                distance_km = data['routes'][0]['summary']['distance'] / 1000  # Convertir en km
                duration_min = data['routes'][0]['summary']['duration'] / 60   # Convertir en minutes
                
                return round(distance_km, 1), round(duration_min, 1)
            else:
                st.warning(f"⚠️ API distance temporairement indisponible")
                return self.estimate_distance_fallback(depart, arrivee)
                
        except Exception as e:
            st.warning(f"⚠️ Calcul de distance approximatif utilisé")
            return self.estimate_distance_fallback(depart, arrivee)
    
    def estimate_distance_fallback(self, depart, arrivee):
        """Estimation de distance fallback si l'API échoue"""
        # Logique d'estimation basée sur la localisation
        peripherique_stations = ['parcelles', 'guediawaye', 'keur massar', 'pikine', 'rufisque', 'diamniadio', 'yoff']
        central_stations = ['plateau', 'dakar', 'medina', 'fann', 'point e', 'mermoz', 'sacré coeur', 'grand dakar']
        
        dep_lower = depart.lower()
        arr_lower = arrivee.lower()
        
        is_depart_peripherique = any(station in dep_lower for station in peripherique_stations)
        is_arrivee_peripherique = any(station in arr_lower for station in peripherique_stations)
        is_depart_central = any(station in dep_lower for station in central_stations)
        is_arrivee_central = any(station in arr_lower for station in central_stations)
        
        if is_depart_peripherique and is_arrivee_peripherique:
            return 18.0, 35  # Long trajet
        elif (is_depart_peripherique and is_arrivee_central) or (is_depart_central and is_arrivee_peripherique):
            return 12.0, 25  # Trajet moyen
        else:
            return 6.0, 15   # Trajet court

class TaxiPriceCalculator:
    def __init__(self, api_key):
        self.distance_calculator = DistanceCalculator(api_key)
        
        # Tarifs taxi Dakar (réalistes)
        self.base_price = 1000    # Prix de prise en charge
        self.price_per_km = 450   # Prix par km
        self.night_surcharge = 1.2  # Majoration nuit (20%)
        self.min_price = 1200     # Prix minimum
        
    def calculate_taxi_price(self, depart, arrivee):
        """Calcule le prix du taxi basé sur la distance réelle"""
        distance_km, duration_min = self.distance_calculator.calculate_real_distance(depart, arrivee)
        
        # Prix de base + prix par km
        base_calculation = self.base_price + (distance_km * self.price_per_km)
        
        # Arrondir à la centaine supérieure
        price = math.ceil(base_calculation / 100) * 100
        
        # Appliquer le prix minimum
        final_price = max(self.min_price, price)
        
        return final_price, distance_km, duration_min

class ScoringModel:
    def __init__(self, df, api_key):
        self.df = df
        self.avg_prix = df['prix'].mean()
        self.avg_rapidite = df['rapidite'].mean()
        self.avg_confort = df['confort'].mean()
        self.taxi_calculator = TaxiPriceCalculator(api_key)
    
    def calculate_score(self, option, preference='équilibré'):
        """Score simple mais équilibré"""
        
        # Définir les poids ÉQUILIBRÉS
        if preference == 'économique':
            weights = {'prix': 0.5, 'rapidite': 0.3, 'confort': 0.2}
        elif preference == 'rapide':
            weights = {'prix': 0.3, 'rapidite': 0.5, 'confort': 0.2}
        elif preference == 'confortable':
            weights = {'prix': 0.3, 'rapidite': 0.2, 'confort': 0.5}
        else:  # équilibré
            weights = {'prix': 0.4, 'rapidite': 0.4, 'confort': 0.2}
        
        # Normalisation
        prix_norm = max(0, 1 - (option['prix'] / (self.avg_prix * 3)))
        rapidite_norm = option['rapidite'] / 10
        confort_norm = option['confort'] / 10
        
        # Score de base
        base_score = (
            prix_norm * weights['prix'] + 
            rapidite_norm * weights['rapidite'] + 
            confort_norm * weights['confort']
        )
        
        # Facteur d'équilibrage par type de transport
        transport_bonus = {
            'BRT': 1.1,
            'TAXI': 1.0,
            'TER': 0.9,
            'DEM-DIKK': 1.2
        }
        
        # Appliquer le bonus selon le type
        transport_type = option['type transport']
        for key, bonus in transport_bonus.items():
            if key in transport_type:
                base_score *= bonus
                break
        
        return min(10, round(base_score * 10, 2))

class SearchEngine:
    def __init__(self, df, scoring_model):
        self.df = df
        self.scoring_model = scoring_model
        self.all_stations = list(set(df['depart'].unique()) | set(df['arrivee'].unique()))
    
    def find_similar_station(self, station_input):
        """Trouve la station la plus similaire"""
        if not station_input:
            return None
            
        station_input = str(station_input).lower().strip()
        
        # Correspondance exacte
        exact_matches = [s for s in self.all_stations if s.lower() == station_input]
        if exact_matches:
            return exact_matches[0]
        
        # Correspondance partielle
        for station in self.all_stations:
            if station_input in station.lower():
                return station
        
        return None
    
    def find_routes(self, depart_input, arrivee_input, preference='équilibré'):
        """Trouve les routes avec recherche flexible"""
        
        depart_corrected = self.find_similar_station(depart_input)
        arrivee_corrected = self.find_similar_station(arrivee_input)
        
        corrections = {}
        if depart_corrected and depart_corrected.lower() != depart_input.lower():
            corrections['depart'] = depart_corrected
        if arrivee_corrected and arrivee_corrected.lower() != arrivee_input.lower():
            corrections['arrivee'] = arrivee_corrected
        
        if not depart_corrected or not arrivee_corrected:
            return None, corrections
        
        # Recherche directe dans le dataset
        mask = (self.df['depart'].str.lower() == depart_corrected.lower()) & \
               (self.df['arrivee'].str.lower() == arrivee_corrected.lower())
        
        options = self.df[mask].copy()
        
        if not options.empty:
            # Calcul des scores pour les options existantes
            options['score'] = options.apply(
                lambda x: self.scoring_model.calculate_score(x, preference), 
                axis=1
            )
            top_3 = options.nlargest(3, 'score')
            return top_3, corrections
        else:
            # Si pas de trajet direct, suggérer le taxi avec prix réel
            return self._suggest_taxi(depart_corrected, arrivee_corrected, preference, corrections)
    
    def _suggest_taxi(self, depart, arrivee, preference, corrections):
        """Suggère une option taxi avec prix calculé en temps réel"""
        taxi_price, distance_km, duration_min = self.scoring_model.taxi_calculator.calculate_taxi_price(depart, arrivee)
        
        # Créer une option taxi réaliste
        taxi_option = pd.DataFrame([{
            'type transport': 'TAXI 🚕',
            'depart': depart,
            'arrivee': arrivee,
            'prix': taxi_price,
            'rapidite': 7.5,  # Taxi généralement rapide
            'confort': 9.0,   # Confort élevé
            'distance_km': distance_km,
            'duree_min': duration_min,
            'is_taxi_suggestion': True
        }])
        
        # Calculer le score
        taxi_option['score'] = taxi_option.apply(
            lambda x: self.scoring_model.calculate_score(x, preference), 
            axis=1
        )
        
        corrections['taxi_suggestion'] = True
        return taxi_option, corrections

# Initialisation
@st.cache_resource
def load_data():
    try:
        df = pd.read_csv("sunuguide_clean_standard.csv")
        preprocessor = DataPreprocessor(df)
        preprocessor.clean_data().create_features()
        return preprocessor.get_data()
    except Exception as e:
        st.error(f"Erreur de chargement: {e}")
        return None

@st.cache_resource
def initialize_models(df, api_key):
    scoring_model = ScoringModel(df, api_key)
    search_engine = SearchEngine(df, scoring_model)
    return scoring_model, search_engine

def main():
    # Initialisation session state
    if 'suggested_depart' not in st.session_state:
        st.session_state.suggested_depart = ""
    if 'suggested_arrivee' not in st.session_state:
        st.session_state.suggested_arrivee = ""
    
    st.sidebar.title("🌍 SunuGuide")
    st.sidebar.markdown("Votre assistant transport intelligent")
    st.sidebar.markdown("---")
    
    # Chargement des données
    df = load_data()
    if df is None:
        st.error("Impossible de charger les données. Vérifiez le fichier CSV.")
        return
    
    # Initialisation des modèles avec votre clé API
    scoring_model, search_engine = initialize_models(df, ORS_API_KEY)
    
    # Stations disponibles
    all_stations = sorted(list(set(df['depart'].unique()) | set(df['arrivee'].unique())))
    
    # Interface principale
    st.title("🚗 SunuGuide - Assistant Transport")
    st.markdown("Trouvez les meilleures options de transport à Dakar")
    
    # Formulaire de recherche
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        default_depart = st.session_state.suggested_depart if st.session_state.suggested_depart else ""
        depart = st.selectbox(
            "📍 Point de départ",
            options=[""] + all_stations,
            index=all_stations.index(default_depart) + 1 if default_depart in all_stations else 0,
        )
        if st.session_state.suggested_depart:
            st.session_state.suggested_depart = ""
    
    with col2:
        default_arrivee = st.session_state.suggested_arrivee if st.session_state.suggested_arrivee else ""
        arrivee = st.selectbox(
            "🎯 Point d'arrivée",
            options=[""] + all_stations,
            index=all_stations.index(default_arrivee) + 1 if default_arrivee in all_stations else 0,
        )
        if st.session_state.suggested_arrivee:
            st.session_state.suggested_arrivee = ""
    
    with col3:
        preference = st.selectbox(
            "⚖️ Préférence",
            options=['Équilibré', 'Économique', 'Rapide', 'Confortable'],
        )
    
    # Bouton de recherche
    if st.button("🔍 Rechercher les trajets", type="primary", use_container_width=True):
        if not depart or not arrivee:
            st.warning("⚠️ Veuillez sélectionner un départ et une arrivée")
        elif depart == arrivee:
            st.warning("⚠️ Le départ et l'arrivée doivent être différents")
        else:
            with st.spinner('Calcul des distances et prix en temps réel...'):
                recommendations, corrections = search_engine.find_routes(
                    depart, arrivee, preference.lower()
                )
            
            st.markdown("---")
            
            # Afficher les corrections
            if corrections:
                if 'depart' in corrections or 'arrivee' in corrections:
                    correction_text = []
                    if 'depart' in corrections:
                        correction_text.append(f"**Départ**: '{depart}' → '{corrections['depart']}'")
                    if 'arrivee' in corrections:
                        correction_text.append(f"**Arrivée**: '{arrivee}' → '{corrections['arrivee']}'")
                    
                    st.info("🔍 " + " | ".join(correction_text))
            
            stations_utilisees = {
                'depart': corrections.get('depart', depart) if corrections else depart,
                'arrivee': corrections.get('arrivee', arrivee) if corrections else arrivee
            }
            
            st.subheader(f"Résultats pour : {stations_utilisees['depart']} → {stations_utilisees['arrivee']}")
            
            if recommendations is None or len(recommendations) == 0:
                st.error("❌ Aucun trajet trouvé pour cet itinéraire")
            else:
                # Afficher les résultats
                for i, (_, option) in enumerate(recommendations.iterrows(), 1):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            transport_type = option['type transport']
                            if 'BRT' in transport_type:
                                icon, color = "🚌", "#1f77b4"
                            elif 'TAXI' in transport_type:
                                icon, color = "🚕", "#2ca02c"
                            elif 'TER' in transport_type:
                                icon, color = "🚆", "#ff7f0e"
                            else:
                                icon, color = "🚗", "#7f7f7f"
                            
                            # Carte d'information
                            st.markdown(f"""
                            <div style="border-left: 4px solid {color}; padding-left: 15px; margin: 10px 0;">
                                <h4 style="margin:0; color: {color};">{icon} {transport_type}</h4>
                                <p style="margin:5px 0; color: #666;">📍 {option['depart']} → {option['arrivee']}</p>
                                {'<p style="margin:5px 0; color: #888;">📏 ' + str(option['distance_km']) + ' km • ⏱️ ' + str(option['duree_min']) + ' min</p>' if 'distance_km' in option and not pd.isna(option['distance_km']) else ''}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.metric("💰 Prix", f"{option['prix']} FCFA")
                        
                        with col3:
                            if 'TAXI' in transport_type:
                                st.metric("📏 Distance", f"{option['distance_km']} km")
                            else:
                                st.metric("⚡ Rapidité", f"{option['rapidite']}/10")
                        
                        with col4:
                            st.metric("⭐ Score", f"{option['score']}/10")
                        
                        # Barre de score
                        st.progress(option['score']/10, text=f"Score: {option['score']}/10")
                        
                        st.markdown("---")

if __name__ == "__main__":
    main()