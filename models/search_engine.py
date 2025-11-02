class SearchEngine:
    def __init__(self, df, scoring_model):
        self.df = df
        self.scoring_model = scoring_model

    def find_routes(self, depart, arrivee, preference="équilibré"):
        # chercher les trajets correspondants
        result = self.scoring_model.get_recommendations(depart, arrivee, preference)
        corrections = {}

        if result is None:
            # suggestions de corrections (ex: erreur d’orthographe)
            corrections = self._suggest_corrections(depart, arrivee)
            return None, corrections

        return result, corrections

    def _suggest_corrections(self, depart, arrivee):
        all_stops = set(self.df["depart"].unique()) | set(self.df["arrivee"].unique())
        corrections = {}

        def closest_match(word):
            from difflib import get_close_matches
            match = get_close_matches(word, all_stops, n=1, cutoff=0.6)
            return match[0] if match else None

        suggestion_depart = closest_match(depart)
        suggestion_arrivee = closest_match(arrivee)

        if suggestion_depart and suggestion_depart.lower() != depart.lower():
            corrections["depart"] = suggestion_depart
        if suggestion_arrivee and suggestion_arrivee.lower() != arrivee.lower():
            corrections["arrivee"] = suggestion_arrivee

        return corrections
