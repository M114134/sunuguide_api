from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models.data_preprocessor import DataPreprocessor
from models.distance_calculator import DistanceCalculator
from models.taxi_price_calculator import TaxiPriceCalculator
from models.scoring_model import ScoringModel
from models.search_engine import SearchEngine
import pandas as pd
from dotenv import load_dotenv
import os

# --- Charger la clé ORS depuis le fichier .env ---
load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")

if not ORS_API_KEY:
    raise ValueError("❌ La clé ORS_API_KEY n'est pas définie dans le fichier .env")

# --- Configuration de l'application ---
app = FastAPI(title="SunuGuide Model API", version="1.0")

# --- Chargement des données et initialisation des modèles ---
print("📦 Chargement des données...")
df = pd.read_csv("sunuguide_clean_standard.csv")
preprocessor = DataPreprocessor(df)
df = preprocessor.clean_data().create_features().get_data()

print("🤖 Initialisation du modèle...")
scoring_model = ScoringModel(df, ORS_API_KEY)
search_engine = SearchEngine(df, scoring_model)

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
    depart = data.depart
    arrivee = data.arrivee
    preference = data.preference.lower()

    recommendations, corrections = search_engine.find_routes(depart, arrivee, preference)

    if recommendations is None or len(recommendations) == 0:
        return {
            "message": "Aucun trajet trouvé pour cet itinéraire",
            "corrections": corrections
        }

    results = recommendations.to_dict(orient="records")
    return {
        "message": "Recommandations trouvées ✅",
        "corrections": corrections,
        "results": results
    }
