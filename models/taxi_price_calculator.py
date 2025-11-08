class TaxiPriceCalculator:
    def __init__(self, tarif_base=200, tarif_km=150):
        self.tarif_base = tarif_base  # prix minimum
        self.tarif_km = tarif_km      # prix par km

    def estimate_price(self, distance_km):
        if distance_km is None:
            return None
        prix = self.tarif_base + (self.tarif_km * distance_km)
        return round(prix)
