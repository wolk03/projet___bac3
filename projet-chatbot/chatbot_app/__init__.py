import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail

# On crée les objets d'extension ici. Ils sont "vides" et seront
# liés à l'application dans la fonction factory.
db = SQLAlchemy()
mail = Mail()
rag_service = None # Sera initialisé une seule fois

def create_app():
    """
    Crée et configure l'instance principale de l'application Flask.
    C'est le modèle "Application Factory".
    """
    global rag_service
    
    app = Flask(__name__, instance_relative_config=True)
    
    # --- 1. CONFIGURATION ---
    # On définit les configurations par défaut et on charge les secrets
    # depuis les variables d'environnement (locales via .env ou sur Render).
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'une-cle-secrete-par-defaut-pour-le-developpement'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Configuration pour Flask-Mail
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_USERNAME')
    )
    
    # --- 2. CONFIGURATION DE LA BASE DE DONNÉES (Adaptative) ---
    # Cette logique choisit la bonne base de données en fonction de l'environnement.
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Environnement de production (Render)
        print("INFO: Variable DATABASE_URL trouvée. Utilisation de PostgreSQL.")
        # SQLAlchemy requiert 'postgresql://' au lieu de 'postgres://' que Render fournit.
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Environnement de développement (votre PC)
        print("INFO: Pas de DATABASE_URL. Utilisation de SQLite en local.")
        instance_path = os.path.join(app.instance_path)
        os.makedirs(instance_path, exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'db.sqlite3')}"
    
    # --- 3. INITIALISATION DES EXTENSIONS ---
    # On lie les extensions (db, mail, etc.) à notre application configurée.
    db.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # --- 4. INITIALISATION DU SERVICE RAG ---
    # On ne l'initialise qu'une seule fois pour toute la durée de vie de l'application.
    if rag_service is None:
        print("INFO: Initialisation du RAGService...")
        from .rag_service import RAGService
        rag_service = RAGService()
        print("INFO: RAGService prêt.")
    
    # --- 5. ENREGISTREMENT DES ROUTES ET CRÉATION DE LA DB ---
    with app.app_context():
        # On importe les routes et modèles ici pour éviter les imports circulaires.
        from . import routes
        from . import models

        # On attache le Blueprint des routes à l'application.
        app.register_blueprint(routes.main_bp)
        
        # Crée toutes les tables définies dans models.py si elles n'existent pas.
        print("INFO: Création des tables de la base de données si nécessaire...")
        db.create_all()
        print("INFO: Tables prêtes.")
        
    print("INFO: Application créée et configurée avec succès.")
    return app
