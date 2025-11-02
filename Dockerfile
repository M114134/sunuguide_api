# Image de base
FROM python:3.14-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers
COPY requirements.txt .
COPY app.py .
COPY models ./models
COPY sunuguide_clean_standard.csv .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port que Uvicorn utilisera
EXPOSE 8000

# Commande pour lancer l'API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
