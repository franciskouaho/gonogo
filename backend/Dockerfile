# Utilisez l'image officielle Python 3.10-slim comme image de base
FROM python:3.10-slim

# Définissez le répertoire de travail dans le conteneur
WORKDIR /backend

# Copiez le fichier des dépendances et installez-les
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Mise à jour de pip
RUN pip install --upgrade pip

# Installez les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Copiez le reste de votre code d'application dans le conteneur
COPY . /backend

# Exposez le port sur lequel uvicorn va s'exécuter
EXPOSE 8000

# Définissez la variable d'environnement pour le chemin Python
ENV PYTHONPATH=/backend

# Commande pour exécuter l'application avec uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
