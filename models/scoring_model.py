import pandas as pd
from .distance_calculator import DistanceCalculator
from .taxi_price_calculator import TaxiPriceCalculator

class ScoringModel:
    def __init__(self, df, ors_api_key):
        self.df = df
        self.distance_calculator = DistanceCalculator(ors_api_key)
        self.taxi_price_calculator = TaxiPriceCalculator()

    def compute_score(self, row, preference="équilibré"):
        # pondération selon la préférence utilisateur
        poids = {
            "rapide": {"rapidite": 0.7, "confort": 0.3},
            "confortable": {"rapidite": 0.3, "confort": 0.7},
            "équilibré": {"rapidite": 0.5, "confort": 0.5}
        }

        prefs = poids.get(preference.lower(), poids["équilibré"])
        score = (row["rapidite"] * prefs["rapidite"]) + (row["confort"] * prefs["confort"])
        return round(score, 2)

    def get_recommendations(self, depart, arrivee, preference="équilibré"):
        filtered = self.df[
            (self.df["depart"].str.lower() == depart.lower()) &
            (self.df["arrivee"].str.lower() == arrivee.lower())
        ]

        if filtered.empty:
            return None

        filtered["score_final"] = filtered.apply(lambda x: self.compute_score(x, preference), axis=1)
        filtered = filtered.sort_values(by="score_final", ascending=False)
        return filtered.head(3)
