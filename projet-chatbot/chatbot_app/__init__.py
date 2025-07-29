import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail

# On crée les extensions SANS les lier à une app
db = SQLAlchemy()
mail = Mail()

def create_app():
    """Crée et configure l'instance de l'application Flask."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'une-cle-secrete-par-defaut'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'db.sqlite3')}",
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_USERNAME'),
        MAIL_DEBUG=True
    )
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Lier les extensions à l'application
    db.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # Importer et initialiser le service RAG
    from .rag_service import RAGService
    app.rag_service = RAGService()
    
    # --- LA MODIFICATION CRUCIALE EST ICI ---
    # On importe et on enregistre les routes À L'INTÉRIEUR de la factory
    from . import routes
    app.register_blueprint(routes.main_bp)

    # Créer la base de données DANS le contexte de l'application
    with app.app_context():
        from . import models # Importer les modèles ici
        db.create_all()
        
    return app