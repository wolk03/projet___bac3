from dotenv import load_dotenv
load_dotenv()
from chatbot_app import create_app

app = create_app()

# La partie if __name__ == '__main__' n'est plus nécessaire pour le déploiement,
# mais gardez-la pour lancer en local. Render n'utilisera pas cette partie.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False) # Mettre debug=False pour la prod