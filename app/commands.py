import click
from .extensions import db, bcrypt
from .models import Product, ContactMessage, StaffUser, Customer, Category, PageVisit, Order
from datetime import date
from sqlalchemy import func

def register_commands(app):
    @app.cli.command('seed')
    def seed_db():
        """Peuple la base de données avec des données de test."""
        print("Suppression des données existantes...")
        Order.query.delete()
        Product.query.delete()
        ContactMessage.query.delete()
        StaffUser.query.delete()
        Customer.query.delete()
        Category.query.delete()

        print("Création des nouvelles catégories...")
        volaille_cat = Category(name='Volaille')
        maraichage_cat = Category(name='Maraîchage')
        db.session.add_all([volaille_cat, maraichage_cat])
        db.session.commit()

        print("Création des nouveaux produits...")
        products = [
            Product(name='Poulet de chair', category=volaille_cat, description='Élevé en plein air, notre poulet de chair est tendre et savoureux.', price=5000, image_file='poulet.jpg'),
            Product(name='Pintade', category=volaille_cat, description='Une viande fine et goûteuse, parfaite pour les repas de fête.', price=7000, image_file='pintade.jpg'),
            Product(name='Oeufs de poule', category=volaille_cat, description='Des oeufs frais du jour, au jaune riche et crémeux.', price=1500, image_file='oeufs.jpg'),
            Product(name='Tomate', category=maraichage_cat, description='Nos tomates sont cultivées en plein champ et cueillies à maturité.', price=1000, image_file='tomate.jpg'),
            Product(name='Oignon vert', category=maraichage_cat, description='Idéal pour relever vos salades et plats cuisinés.', price=500, image_file='oignon.jpg')
        ]
        db.session.add_all(products)
        db.session.commit()
        print("Les produits ont été ajoutés avec succès !")

    @app.cli.command('create-db')
    def create_db():
        """Crée toutes les tables de la base de données."""
        db.create_all()
        print("Base de données et tables créées avec succès !")

    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('password')
    def create_admin(username, email, password):
        """Crée un utilisateur administrateur."""
        if StaffUser.query.filter_by(username=username).first():
            print(f"L'utilisateur '{username}' existe déjà.")
            return
        if StaffUser.query.filter_by(email=email).first():
            print(f"L'email '{email}' existe déjà.")
            return
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = StaffUser(username=username, email=email, password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()
        print(f"L'utilisateur administrateur '{username}' avec l'email '{email}' a été créé avec succès.")

    @app.cli.command('clear-visits')
    def clear_visits():
        """Supprime toutes les visites enregistrées pour la journée en cours."""
        today = date.today()
        deleted_count = PageVisit.query.filter(func.date(PageVisit.timestamp) == today).delete()
        db.session.commit()
        print(f"Supprimé {deleted_count} enregistrements de visites pour le {today.strftime('%d/%m/%Y')}.")
