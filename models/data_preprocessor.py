import pandas as pd

class DataPreprocessor:
    def __init__(self, df):
        self.df = df.copy()
    
    def clean_data(self):
        # Nettoyage des colonnes texte
        for col in ['depart', 'arrivee', 'type transport']:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip().str.lower()
        
        # Remplir les valeurs manquantes
        self.df['rapidite'] = self.df['rapidite'].fillna(5.0)
        self.df['confort'] = self.df['confort'].fillna(5.0)
        self.df['type transport'] = self.df['type transport'].fillna("inconnu")

        # Supprimer les doublons
        self.df = self.df.drop_duplicates(subset=['depart', 'arrivee', 'type transport'])
        return self
    
    def create_features(self):
        # Créer une catégorie de prix
        self.df['categorie_prix'] = pd.cut(
            self.df['prix'], 
            bins=[0, 500, 2000, 50000],
            labels=['Économique', 'Moyen', 'Cher']
        )

        # Calculer un score moyen
        self.df['score_basique'] = (self.df['rapidite'] + self.df['confort']) / 2
        return self
    
    def get_data(self):
        return self.df
