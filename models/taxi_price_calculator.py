class TaxiPriceCalculator:
    def __init__(self, base_price=500, price_per_km=150):
        self.base_price = base_price
        self.price_per_km = price_per_km

    def estimate_price(self, distance_km):
        if distance_km is None:
            return None
        return round(self.base_price + distance_km * self.price_per_km, 2)
