#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Le contexte de l'application est nécessaire pour que db.create_all() fonctionne
flask shell <<EOF
from chatbot_app import db
db.create_all()
EOF