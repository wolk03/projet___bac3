from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from . import db # On importe 'db' depuis le fichier app.py principal
from .models import User, Conversation, Message
from chatbot_app.utils import generate_confirmation_token, confirm_token, send_email # Le chemin complet est plus sûr
import logging

main_bp = Blueprint('main', __name__)
@main_bp.route('/')
# @main_bp.route('/index')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.home'))
    return render_template('splash.html')

@main_bp.route('/main.auth')
def auth():
    if 'user_id' in session:
        return redirect(url_for('main.main.home'))
    return render_template('auth.html')

@main_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        # --- NOUVELLE VÉRIFICATION ---
        if not user.email_confirmed:
            flash('Veuillez confirmer votre adresse email avant de vous connecter.', 'warning')
            return redirect(url_for('main.auth'))
        # -----------------------------
            
        session['user_id'] = user.id
        session['user_name'] = user.get_full_name()
        return redirect(url_for('main.home'))
    else:
        flash('Email ou mot de passe incorrect', 'error')
        return redirect(url_for('main.auth'))

@main_bp.route('/register', methods=['POST'])
def register():
    # ... (récupération des données du formulaire : nom, email, etc.)
    nom = request.form.get('nom')
    postnom = request.form.get('postnom')
    prenom = request.form.get('prenom')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # ... (toute votre validation : champs vides, mots de passe identiques, etc.)

    # Vérifier si l'utilisateur existe déjà
    if User.query.filter_by(email=email).first():
        flash('Un compte avec cet email existe déjà.', 'error')
        return redirect(url_for('main.auth'))
    
    # Créer l'utilisateur
    user = User(nom=nom, postnom=postnom, prenom=prenom, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # --- BLOC D'ENVOI D'EMAIL SANS TRY...EXCEPT ---
    # Si une erreur se produit ici, l'application va crasher et afficher la trace d'erreur complète.
    print("Tentative d'envoi de l'email de confirmation...")
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('main.confirm_email', token=token, _external=True)
    html = render_template('emails/confirm_email.html', user=user, confirm_url=confirm_url)
    
    send_email(user.email, "Veuillez confirmer votre email", html)
    
    print("Email envoyé avec succès (selon le code).")

    flash('Un email de confirmation a été envoyé à votre adresse.', 'success')
    return redirect(url_for('main.auth'))
@main_bp.route('/send_confirmation_email/<int:user_id>')
def send_confirmation_email(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('Utilisateur non trouvé.', 'error')
        return redirect(url_for('main.auth'))
    
    token = generate_confirmation_token(user.email)
    confirmation_url = url_for('main.confirm_email', token=token, _external=True)
    
    html_content = f"""
    <h1>Bienvenue {user.get_full_name()} !</h1>
    <p>Merci de vous être inscrit. Veuillez confirmer votre adresse email en cliquant sur le lien ci-dessous :</p>
    <a href="{confirmation_url}">Confirmer mon email</a>
    """
    
    try:
        send_email(user.email, "Confirmation de votre compte", html_content)
        flash('Un email de confirmation a été envoyé.', 'success')
    except Exception as e:
        logging.error(f"Error sending confirmation email: {e}")
        flash('Erreur lors de l\'envoi de l\'email de confirmation.', 'error')
    
    return redirect(url_for('main.auth'))
@main_bp.route('/test_email')
def test_email_route():
    try:
        print("--- DÉBUT DU TEST D'ENVOI D'EMAIL ---")
        
        # On importe la fonction send_email ici pour être sûr
        from .utils import send_email
        
        # On crée un email de test simple
        html_content = "<h1>Ceci est un test</h1><p>Si vous recevez cet email, cela signifie que Flask-Mail est correctement configuré.</p>"
        
        # IMPORTANT: Mettez une VRAIE adresse email à laquelle vous avez accès
        recipient_email = "votre_adresse_email_personnelle@gmail.com"
        
        print(f"Envoi de l'email de test à {recipient_email}...")
        
        # On appelle la fonction d'envoi
        send_email(recipient_email, "Email de Test depuis Flask", html_content)
        
        print("--- La fonction send_email a été appelée sans crash. ---")
        
        # Si on arrive ici, cela signifie qu'aucune erreur n'a été levée.
        return "<h1>Test d'envoi d'email terminé !</h1><p>La fonction a été appelée. Vérifiez votre boîte de réception et le terminal pour les erreurs.</p>"

    except Exception as e:
        # Si une erreur se produit, on l'affiche directement dans le navigateur
        print(f"!!! ERREUR ATTRAPÉE PENDANT LE TEST D'EMAIL : {e} !!!")
        return f"<h1>Une erreur est survenue</h1><p>Voici l'erreur : <pre>{e}</pre></p>", 500
    

# --- NOUVELLE ROUTE POUR CONFIRMER L'EMAIL ---
@main_bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('Le lien de confirmation est invalide ou a expiré.', 'danger')
        return redirect(url_for('main.auth'))
        
    user = User.query.filter_by(email=email).first_or_404()
    
    if user.email_confirmed:
        flash('Compte déjà confirmé. Veuillez vous connecter.', 'success')
    else:
        user.email_confirmed = True
        db.session.commit()
        flash('Votre compte a été confirmé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        
    return redirect(url_for('main.auth'))

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('main.index'))


# --- Routes Principales de l'Application ---

@main_bp.route('/main.home')
def home():
    if 'user_id' not in session: 
        return redirect(url_for('main.auth'))
    
    user = User.query.get(session['user_id'])
    
    # --- NOUVELLE VÉRIFICATION ---
    # Si l'utilisateur n'existe plus dans la base de données,
    # on nettoie la session et on le renvoie à la page de connexion.
    if not user:
        session.clear()
        flash("Votre session a expiré ou votre compte est introuvable. Veuillez vous reconnecter.", "warning")
        return redirect(url_for('main.auth'))
    # -----------------------------
    
    return render_template('home.html', user=user)

@main_bp.route('/chat')
@main_bp.route('/chat/<int:conversation_id>')
def chat(conversation_id=None):
    if 'user_id' not in session: return redirect(url_for('main.auth'))
    user = User.query.get(session['user_id'])
    
    conversation = None
    messages = []
    if conversation_id:
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
        if conversation:
            messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp).all()
    
    return render_template('chat.html', user=user, conversation=conversation, messages=messages)

@main_bp.route('/new_conversation', methods=['POST'])
def new_conversation():
    if 'user_id' not in session: return redirect(url_for('main.auth'))
    user = User.query.get(session['user_id'])
    conversation = Conversation(user_id=user.id)
    db.session.add(conversation)
    db.session.commit()
    return redirect(url_for('main.chat', conversation_id=conversation.id))


# --- Route pour le Chatbot (LA PARTIE MODIFIÉE) ---

@main_bp.route('/main.profile')
def profile():
    """Affiche la page de profil de l'utilisateur avec son historique de conversations."""
    # Sécurité : vérifier que l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    # Récupérer l'utilisateur depuis la base de données
    user = User.query.get(session['user_id'])
    if not user:
        # Si l'utilisateur a été supprimé, on nettoie la session
        session.clear()
        return redirect(url_for('main.auth'))
    
    # Récupérer l'historique des conversations de l'utilisateur
    conversations = Conversation.query.filter_by(user_id=user.id).order_by(Conversation.updated_at.desc()).all()
    
    # Afficher le template du profil avec les données de l'utilisateur
    return render_template('profile.html', user=user, conversations=conversations)


@main_bp.route('/main.settings')
def settings():
    """Affiche la page des paramètres."""
    # Sécurité : vérifier que l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    # Récupérer l'utilisateur pour pouvoir afficher son nom, etc.
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.auth'))
    
    # Afficher le template des paramètres
    return render_template('settings.html', user=user)


@main_bp.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorisé'}), 401
    
    conversation_id = request.form.get('conversation_id')
    message_content = request.form.get('message')
    
    if not conversation_id or not message_content:
        flash('Erreur lors de l\'envoi du message.', 'error')
        return redirect(request.referrer or url_for('main.home'))
        
    user = User.query.get(session['user_id'])
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    
    if not conversation:
        flash('Conversation non trouvée.', 'error')
        return redirect(url_for('main.home'))
    
    try:
        # 1. Sauvegarder le message de l'utilisateur
        user_message = Message(content=message_content, is_user=True, conversation_id=conversation.id)
        db.session.add(user_message)
        
        # 2. Obtenir la réponse du service RAG (attaché à l'application)
        rag_service = current_app.rag_service
        bot_response = rag_service.ask(message_content)
        
        # 3. Sauvegarder la réponse du bot
        bot_message = Message(content=bot_response, is_user=False, conversation_id=conversation.id)
        db.session.add(bot_message)
        
        # 4. Mettre à jour le titre de la conversation si c'est le premier message
        if conversation.title == "Nouvelle conversation":
            title_words = message_content.split()[:5]
            conversation.title = ' '.join(title_words) + ('...' if len(title_words) == 5 else '')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error sending message: {e}")
        flash('Une erreur est survenue lors de la communication avec le chatbot.', 'error')

    return redirect(url_for('main.chat', conversation_id=conversation_id))

@main_bp.route('/update_profile', methods=['POST'])
def update_profile():
    """Met à jour les informations du profil de l'utilisateur."""
    # Sécurité : vérifier que l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.auth'))
    
    # Récupérer les données du formulaire
    nom = request.form.get('nom')
    postnom = request.form.get('postnom')
    prenom = request.form.get('prenom')
    email = request.form.get('email')
    
    # Validation simple
    if not all([nom, postnom, prenom, email]):
        flash('Veuillez remplir tous les champs', 'error')
        return redirect(url_for('main.profile'))
    
    # Vérifier si l'email est déjà pris par un autre utilisateur
    existing_user = User.query.filter(User.email == email, User.id != user.id).first()
    if existing_user:
        flash('Cet email est déjà utilisé par un autre compte', 'error')
        return redirect(url_for('main.profile'))
    
    # Mettre à jour les informations de l'utilisateur
    try:
        user.nom = nom
        user.postnom = postnom
        user.prenom = prenom
        user.email = email
        
        db.session.commit()
        
        # Mettre à jour le nom dans la session pour l'affichage
        session['user_name'] = user.get_full_name()
        
        flash('Profil mis à jour avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating profile: {e}")
        flash('Erreur lors de la mise à jour du profil', 'error')
    
    # Rediriger vers la page de profil après la mise à jour
    return redirect(url_for('main.profile'))


@main_bp.route('/delete_conversation/<int:conversation_id>', methods=['POST'])
def delete_conversation(conversation_id):
    """Supprime une conversation et tous les messages associés."""
    # Sécurité : vérifier que l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    # Trouver la conversation à supprimer, en s'assurant qu'elle appartient bien à l'utilisateur connecté
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=session['user_id']).first()
    
    if conversation:
        try:
            # SQLAlchemy gère la suppression en cascade des messages
            db.session.delete(conversation)
            db.session.commit()
            flash('Conversation supprimée avec succès.', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting conversation: {e}")
            flash('Erreur lors de la suppression de la conversation.', 'error')
    else:
        flash('Conversation non trouvée ou vous n\'avez pas la permission de la supprimer.', 'warning')
    
    # Rediriger vers la page de profil après la suppression
    return redirect(url_for('main.profile'))


@main_bp.route('/change_password', methods=['POST'])
def change_password():
    """Gère le changement de mot de passe de l'utilisateur."""
    # Sécurité : vérifier que l'utilisateur est connecté
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.auth'))
    
    # Récupérer les données du formulaire
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validation
    if not all([current_password, new_password, confirm_password]):
        flash('Veuillez remplir tous les champs', 'error')
        return redirect(url_for('main.settings'))
    
    if not user.check_password(current_password):
        flash('Le mot de passe actuel est incorrect', 'error')
        return redirect(url_for('main.settings'))
    
    if new_password != confirm_password:
        flash('Les nouveaux mots de passe ne correspondent pas', 'error')
        return redirect(url_for('main.settings'))
    
    if len(new_password) < 6:
        flash('Le nouveau mot de passe doit contenir au moins 6 caractères', 'error')
        return redirect(url_for('main.settings'))
    
    # Mettre à jour le mot de passe
    try:
        user.set_password(new_password)
        db.session.commit()
        flash('Mot de passe modifié avec succès !', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error changing password: {e}")
        flash('Erreur lors de la modification du mot de passe.', 'error')
    
    return redirect(url_for('main.settings'))

@main_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        # Pour une vraie app, on utiliserait un token (JWT)
        # Pour commencer, on peut juste renvoyer un succès
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'name': user.get_full_name()
            }
        }), 200
    else:
        return jsonify({'success': False, 'message': 'Email ou mot de passe incorrect'}), 401
    
# Fichier: routes.py
# ... (tous vos imports et routes existants)

# --- NOUVELLE ROUTE API POUR L'APPLICATION MOBILE ET CLIENTS EXTERNES ---
@main_bp.route('/api/ask', methods=['POST'])
def api_ask():
    """
    Cette route prend du JSON en entrée et renvoie du JSON en sortie.
    Elle est parfaite pour être appelée par une application mobile.
    """
    # Récupérer les données JSON envoyées par Flutter
    data = request.get_json()
    
    # Validation simple
    if not data or 'question' not in data or not data['question'].strip():
        return jsonify({'error': 'La question est manquante ou vide'}), 400

    user_question = data.get('question')
    
    # Utiliser le même service RAG que vous avez déjà initialisé
    rag_service = current_app.rag_service
    response_text = rag_service.ask(user_question)
    
    # Renvoyer la réponse au format JSON
    return jsonify({'answer': response_text})

# ... (vos autres routes restent inchangées)