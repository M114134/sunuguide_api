import requests

class DistanceCalculator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    def get_distance(self, depart, arrivee):
        try:
            url = f"{self.base_url}?api_key={self.api_key}&start={depart[1]},{depart[0]}&end={arrivee[1]},{arrivee[0]}"
            response = requests.get(url)
            data = response.json()

            distance_m = data["features"][0]["properties"]["segments"][0]["distance"]
            duration_s = data["features"][0]["properties"]["segments"][0]["duration"]

            return {
                "distance_km": round(distance_m / 1000, 2),
                "duree_min": round(duration_s / 60, 2)
            }
        except Exception as e:
            print(f"Erreur DistanceCalculator: {e}")
            return {"distance_km": None, "duree_min": None}
