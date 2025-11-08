# app.py

from fastapi import FastAPI
from pydantic import BaseModel
from models.data_preprocessor import DataPreprocessor
from models.distance_calculator import DistanceCalculator
from models.taxi_price_calculator import TaxiPriceCalculator
from models.scoring_model import ScoringModel
from models.search_engine import SearchEngine
import pandas as pd

# --- Configuration de l'application ---
app = FastAPI(title="SunuGuide Model API", version="2.0")

# --- Clé API OpenRouteService ---
ORS_API_KEY = "TA_CLE_API_ICI"

# --- Chargement des données et initialisation des modèles ---
print("📦 Chargement des données...")
df = pd.read_csv("sunuguide_clean_standard.csv")

preprocessor = DataPreprocessor(df)
df = preprocessor.clean_data().create_features().get_data()

print("🤖 Initialisation du modèle...")
distance_calculator = DistanceCalculator(ORS_API_KEY)
scoring_model = ScoringModel(df, ORS_API_KEY)
search_engine = SearchEngine(df, scoring_model)
taxi_price_calculator = TaxiPriceCalculator()

# --- Schéma d’entrée ---
class RequestData(BaseModel):
    depart: str
    arrivee: str
    preference: str = "équilibré"

# --- Endpoint racine ---
@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API SunuGuide 🚗"}

# --- Endpoint de prédiction ---
@app.post("/predict")
def predict(data: RequestData):
    depart = data.depart.strip().lower()
    arrivee = data.arrivee.strip().lower()
    preference = data.preference.lower()

    # Recherche des trajets correspondants
    recommendations, corrections = search_engine.find_routes(depart, arrivee, preference)

    if recommendations is None or len(recommendations) == 0:
        return {
            "message": "Aucun trajet trouvé pour cet itinéraire",
            "corrections": corrections
        }

    results = []
    for _, row in recommendations.iterrows():
        try:
            # Si vous n'avez pas les coordonnées exactes, vous pouvez générer ou utiliser des valeurs fictives
            depart_coords = [14.6937, -17.4441]   # Exemple Dakar
            arrivee_coords = [14.7167, -17.4677]  # Exemple Plateau

            distance_info = distance_calculator.get_distance(depart_coords, arrivee_coords)
            distance_km = distance_info["distance_km"]
            duree_min = distance_info["duree_min"]

            prix_estime = taxi_price_calculator.estimate_price(distance_km)

            results.append({
                "transport": row.get("type transport", "N/A"),
                "depart": depart.capitalize(),
                "arrivee": arrivee.capitalize(),
                "distance_km": distance_km,
                "duree_min": duree_min,
                "prix_estime": prix_estime
            })

        except Exception as e:
            print(f"Erreur calcul trajet : {e}")

    return {
        "message": "Recommandations calculées ✅",
        "corrections": corrections,
        "results": results
    }
