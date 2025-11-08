class SearchEngine:
    def __init__(self, df, scoring_model):
        self.df = df
        self.scoring_model = scoring_model

    def find_routes(self, depart, arrivee, preference="équilibré"):
        result = self.scoring_model.get_recommendations(depart, arrivee, preference)
        corrections = {}

        if result is None or result.empty:
            corrections = self._suggest_corrections(depart, arrivee)
            return None, corrections

        return result, corrections

    def _suggest_corrections(self, depart, arrivee):
        from difflib import get_close_matches
        all_stops = set(self.df["depart"].unique()) | set(self.df["arrivee"].unique())
        corrections = {}

        def closest_match(word):
            match = get_close_matches(word.lower(), all_stops, n=1, cutoff=0.6)
            return match[0] if match else None

        suggestion_depart = closest_match(depart)
        suggestion_arrivee = closest_match(arrivee)

        if suggestion_depart and suggestion_depart.lower() != depart.lower():
            corrections["depart"] = suggestion_depart
        if suggestion_arrivee and suggestion_arrivee.lower() != arrivee.lower():
            corrections["arrivee"] = suggestion_arrivee

        return corrections
