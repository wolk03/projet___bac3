import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail
# On ne charge PAS dotenv ici, car Render gère les variables.

db = SQLAlchemy()
mail = Mail()
rag_service = None

def create_app():
    global rag_service
    app = Flask(__name__, instance_relative_config=True)
    
    # La configuration lit les variables directement depuis l'environnement du serveur
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        # ...
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        # ...
    )
    # ...
    
    # Lier les extensions
    db.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # L'appel à RAGService se fait ici. À ce moment, les os.environ.get
    # devraient avoir fonctionné.
    if rag_service is None:
        from .rag_service import RAGService
        rag_service = RAGService()
    
    # ... (le reste)
    return app
