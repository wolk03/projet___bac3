# Fichier: chatbot_app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail

# On crée les objets d'extension ici. Ils sont "vides" pour l'instant.
db = SQLAlchemy()
mail = Mail()
# Le service RAG sera initialisé plus tard car il a besoin de la config
rag_service = None 

def create_app():
    """Crée et configure l'instance de l'application Flask."""
    global rag_service
    
    app = Flask(__name__, instance_relative_config=True)
    
    # --- Configuration ---
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'une-cle-secrete-par-defaut'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'db.sqlite3')}",
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_USERNAME')
    )
    os.makedirs(app.instance_path, exist_ok=True)
    
    # --- Lier les extensions à l'application ---
    db.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # Initialiser le service RAG
    if rag_service is None:
        from .rag_service import RAGService
        rag_service = RAGService()
    
    # --- Enregistrement des routes et création de la DB ---
    with app.app_context():
        # On importe les routes ICI, APRES que tout soit initialisé
        from . import routes
        app.register_blueprint(routes.main_bp)
        
        # On importe les modèles pour que SQLAlchemy les connaisse
        from . import models
        db.create_all()
        
    return app
