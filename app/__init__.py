# -*- coding: utf-8 -*-

import os
import uuid
import click
from .commands import register_commands
from flask import Flask, render_template, request, session, g
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_assets import Environment, Bundle
from whitenoise import WhiteNoise

# Charger les variables d'environnement
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(dotenv_path=os.path.join(basedir, '.env'))

from .extensions import db, bcrypt, login_manager, mail, moment, csrf, migrate, assets

# Configuration du LoginManager
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

# Allowed extensions for image upload

def create_app(config_overrides=None):
    """Crée et configure une instance de l'application Flask."""
    app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'), static_folder=os.path.join(basedir, 'static'))

    # Configuration de l'application
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        WTF_CSRF_ENABLED=True,
        
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'site.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MOMENT_DEFAULT_LOCALE='fr',
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.environ.get('EMAIL_USER'),
        MAIL_PASSWORD=os.environ.get('EMAIL_PASS'),
        MAIL_DEFAULT_SENDER=os.environ.get('EMAIL_USER'),
        UPLOAD_FOLDER=os.path.join(basedir, 'static/images'),
        ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif', 'webp'},
        STRIPE_PUBLIC_KEY=os.environ.get('STRIPE_PUBLIC_KEY'),
        STRIPE_SECRET_KEY=os.environ.get('STRIPE_SECRET_KEY'),
        STRIPE_ENDPOINT_SECRET=os.environ.get('STRIPE_ENDPOINT_SECRET'),
        ENABLE_ORANGE_MONEY=os.environ.get('ENABLE_ORANGE_MONEY') == '1',
        ENABLE_WAVE_MONEY=os.environ.get('ENABLE_WAVE_MONEY') == '1',
    )

    if config_overrides:
        app.config.update(config_overrides)

    # Initialiser les extensions avec l'application
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    assets.init_app(app)
    if app.config["TESTING"]:
        Talisman(app, force_https=False)
    else:
        Talisman(
            app,
            content_security_policy={
                'default-src': "'self'",
                'style-src': [
                    "'self'",
                    "'unsafe-inline'",
                    'https://cdnjs.cloudflare.com',
                    'https://cdn.jsdelivr.net'
                ],
                'script-src': [
                    "'self'",
                    "'unsafe-inline'",
                    'https://cdnjs.cloudflare.com',
                    'https://cdn.jsdelivr.net'
                ],
                'font-src': ["'self'", 'https://cdnjs.cloudflare.com'],
                'frame-src': ["'self'", 'https://www.youtube.com']
            }
        )

    # Whitenoise for static files
    if not app.config.get('TESTING'):
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(basedir, 'static'))

    # Définition des bundles d'assets
    css_bundle = Bundle(
        'css/bootstrap.min.css',
        'css/custom.css',
        filters='cssmin',
        output='gen/packed.css'
    )
    js_bundle = Bundle(
        'js/bootstrap.bundle.min.js',
        filters='jsmin',
        output='gen/packed.js'
    )

    # Enregistrement des bundles
    if 'css_all' not in assets:
        assets.register('css_all', css_bundle)
    if 'js_all' not in assets:
        assets.register('js_all', js_bundle)

    from . import models

    with app.app_context():
        # Importer les modèles ici pour éviter les importations circulaires
        from .models import StaffUser, Customer, Product, ContactMessage, Category, PageVisit, Banner, NewsletterSubscriber
        from .forms import NewsletterForm

        @login_manager.user_loader
        def load_user(user_id_str):
            try:
                user_type, user_id = user_id_str.split('-')
                user_id = int(user_id)
            except (ValueError, TypeError):
                return None

            if user_type == 'staff':
                return db.session.get(StaffUser, user_id)
            elif user_type == 'customer':
                return db.session.get(Customer, user_id)
            return None

        @app.context_processor
        def inject_user_type():
            return dict(isinstance=isinstance, StaffUser=StaffUser, Customer=Customer)

        @app.context_processor
        def inject_active_banners():
            active_banners = db.session.execute(Banner.get_active_banners().order_by(Banner.position, Banner.created_at.desc())).scalars().all()
            return dict(active_banners=active_banners)

        @app.context_processor
        def inject_newsletter_form():
            return dict(newsletter_form=NewsletterForm())

        # Gestion des erreurs de l'application
        @app.before_request
        def record_visit():
            if app.config.get('TESTING'):
                return
            # On ne veut pas enregistrer les visites pour les fichiers statiques
            # ou pour les requêtes de l'API de webhook Stripe, pour ne pas polluer les stats.
            if (request.path.startswith('/static') or
                request.path.startswith('/auth/stripe-webhook')):
                return

            # Gérer l'identifiant de session
            session_id = request.cookies.get('session_id')
            if not session_id:
                session_id = str(uuid.uuid4())
                # Utiliser g pour stocker le session_id pour la réponse
                g.session_id = session_id

            # Enregistre la visite
            visit = PageVisit(session_id=session_id)
            db.session.add(visit)
            db.session.commit()

        @app.after_request
        def set_session_cookie(response):
            if hasattr(g, 'session_id'):
                # Définir le cookie pour 30 minutes d'inactivité
                # max_age est en secondes (30 minutes * 60 secondes)
                response.set_cookie('session_id', g.session_id, max_age=30 * 60)
            return response

        @app.errorhandler(404)
        def not_found_error(error):
            """Gère les erreurs 404 (page non trouvée)."""
            return render_template('404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            """Gère les erreurs 500 (erreur interne du serveur)."""
            db.session.rollback()  # Annule la transaction en cas d'erreur
            return render_template('500.html'), 500

        # Enregistrer les commandes CLI
        register_commands(app)

        # Importer et enregistrer les Blueprints
        from .main import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')

        from .admin import admin as admin_blueprint
        app.register_blueprint(admin_blueprint, url_prefix='/admin')

        from .products import products as products_blueprint
        app.register_blueprint(products_blueprint)

        from .cart import cart as cart_blueprint
        app.register_blueprint(cart_blueprint)

        from .wishlist import wishlist as wishlist_blueprint
        app.register_blueprint(wishlist_blueprint, url_prefix='/wishlist')

        @app.template_filter('format_price')
        def format_price_filter(value):
            return "{:,.2f} FCFA".format(value)

        return app
