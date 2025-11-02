# models/data_preprocessor.py

import pandas as pd

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
