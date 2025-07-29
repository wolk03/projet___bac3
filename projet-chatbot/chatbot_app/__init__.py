import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'une-cle-secrete-par-defaut'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'db.sqlite3')}"
    )
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialisation des extensions
    db.init_app(app)
    CORS(app)
    
    # --- MODIFICATION CLÉ : INITIALISATION PARESSEUSE ---
    # On ne crée pas l'instance de RAGService tout de suite.
    # On la met dans un conteneur.
    app.rag_service_container = {}

    @app.before_request
    def get_rag_service():
        # Cette fonction sera appelée avant chaque requête.
        # Si le service n'est pas encore initialisé, on le crée.
        if 'rag_service' not in app.rag_service_container:
            print("Initialisation paresseuse du RAGService...")
            from .rag_service import RAGService
            app.rag_service_container['rag_service'] = RAGService()
            print("RAGService prêt.")

    # On attache une propriété pour y accéder facilement
    @property
    def rag_service(self):
        return self.rag_service_container.get('rag_service')
    app.rag_service = rag_service
    # ----------------------------------------------------

    with app.app_context():
        from . import routes
        app.register_blueprint(routes.main_bp)
        from . import models
        db.create_all()
        
    return app
