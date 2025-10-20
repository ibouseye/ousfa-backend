'''
Ce fichier enregistre les commandes CLI personnalisées pour l'application.
'''
import click
from .extensions import db, bcrypt
from .models import StaffUser, PageVisit
from datetime import date
from sqlalchemy import func

# Importer le groupe de commandes 'seed' depuis le nouveau fichier seed.py
from seed import seed

def register_commands(app):
    # Enregistrer le nouveau groupe de commandes (qui contient populate, reset, full-reset)
    app.cli.add_command(seed)

    @app.cli.command('create-db')
    def create_db():
        """Crée toutes les tables de la base de données."""
        db.create_all()
        click.echo("Base de données et tables créées avec succès !")

    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('password')
    def create_admin(username, email, password):
        """Crée un utilisateur administrateur."""
        if StaffUser.query.filter_by(username=username).first():
            click.echo(f"L'utilisateur '{username}' existe déjà.")
            return
        if StaffUser.query.filter_by(email=email).first():
            click.echo(f"L'email '{email}' existe déjà.")
            return
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = StaffUser(username=username, email=email, password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()
        click.echo(click.style(f"L'utilisateur administrateur '{username}' a été créé.", fg='green'))

    @app.cli.command('clear-visits')
    def clear_visits():
        """Supprime toutes les visites enregistrées pour la journée en cours."""
        today = date.today()
        try:
            deleted_count = db.session.query(PageVisit).filter(func.date(PageVisit.timestamp) == today).delete()
            db.session.commit()
            click.echo(f"Supprimé {deleted_count} enregistrements de visites pour le {today.strftime('%d/%m/%Y')}.")
        except Exception as e:
            db.session.rollback()
            click.echo(click.style(f"Une erreur est survenue : {e}", fg='red'))