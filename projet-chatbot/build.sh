#!/usr/bin/env bash
# Permet au script de s'arrêter en cas d'erreur
set -o errexit

# Mettre à jour pip et installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Créer les tables de la base de données.
# On utilise 'flask shell' pour exécuter du code Python dans le contexte de l'application.
# C'est une méthode robuste pour s'assurer que db.create_all() est appelé correctement.
flask shell <<EOF
from chatbot_app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
exit()
EOF
