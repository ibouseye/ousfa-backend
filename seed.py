'''
Ce script fournit des commandes CLI pour peupler et réinitialiser la base de données.
'''
import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import (
    Product, Category, StaffUser, Customer, Order, OrderItem,
    ContactMessage, PageVisit, Banner, Post, PostImage, ProductImage,
    Review, ReviewVote, WishlistItem, CartItem, SmartShopping,
    SmartShoppingReservation, PageContent, Milestone, NewsletterSubscriber, Newsletter
)

# Création d'un groupe de commandes 'seed'
@click.group()
def seed():
    """Commandes pour la gestion des données de la base."""
    pass

@seed.command()
@with_appcontext
def populate():
    """Peuple la base de données avec des données initiales."""
    click.echo("Création des catégories et produits de base...")

    # --- Création des catégories ---
    cat_volaille = Category.query.filter_by(name='Volaille').first()
    if not cat_volaille:
        cat_volaille = Category(name='Volaille')
        db.session.add(cat_volaille)

    cat_maraichage = Category.query.filter_by(name='Maraîchage').first()
    if not cat_maraichage:
        cat_maraichage = Category(name='Maraîchage')
        db.session.add(cat_maraichage)
    
    db.session.commit()

    # --- Création des produits ---
    products_to_add = {
        'Poulet de chair': {'category': cat_volaille, 'description': 'Élevé en plein air, tendre et savoureux.', 'price': 5000, 'image_file': 'poulet.jpg', 'stock': 50},
        'Pintade': {'category': cat_volaille, 'description': 'Viande fine et goûteuse.', 'price': 7000, 'image_file': 'pintade.jpg', 'stock': 30},
        'Oeufs de poule': {'category': cat_volaille, 'description': 'Oeufs frais du jour.', 'price': 1500, 'image_file': 'oeufs.jpg', 'stock': 100},
        'Tomate': {'category': cat_maraichage, 'description': 'Cultivées en plein champ.', 'price': 1000, 'image_file': 'tomate.jpg', 'stock': 200},
        'Oignon vert': {'category': cat_maraichage, 'description': 'Idéal pour relever vos plats.', 'price': 500, 'image_file': 'oignon.jpg', 'stock': 150}
    }

    for name, data in products_to_add.items():
        if not Product.query.filter_by(name=name).first():
            product = Product(name=name, **data)
            db.session.add(product)

    db.session.commit()
    click.echo("Peuplement des produits et catégories terminé.")

    # --- Création des pages de contenu ---
    click.echo("Création des pages de contenu par défaut...")
    about_us_page = PageContent.query.filter_by(page_name='about-us').first()
    if not about_us_page:
        about_us_page = PageContent(
            page_name='about-us',
            title='Qui sommes-nous ?',
            subtitle='''L'histoire de notre ferme et de notre passion.''',
            body='''<p>Bienvenue sur notre page ! Ici, vous pouvez écrire l'histoire de votre projet, vos valeurs, et ce qui rend votre ferme unique.</p>
<p>Parlez de votre engagement envers la qualité, l'agriculture durable, et le bien-être animal. C'est l'endroit idéal pour créer un lien de confiance avec vos clients.</p>'''
        )
        db.session.add(about_us_page)
    
    # --- Création des pages FAQ, Témoignages et Partenaires ---
    click.echo("Création des pages FAQ, Témoignages et Partenaires...")
    faq_page = PageContent.query.filter_by(page_name='faq').first()
    if not faq_page:
        faq_page = PageContent(
            page_name='faq',
            title='Foire Aux Questions',
            subtitle='Vos questions, nos réponses.',
            body='''<p>Ici, vous trouverez les réponses aux questions les plus fréquemment posées.</p>
<p>N\'hésitez pas à nous contacter si vous ne trouvez pas ce que vous cherchez.</p>'''
        )
        db.session.add(faq_page)

    testimonials_page = PageContent.query.filter_by(page_name='testimonials').first()
    if not testimonials_page:
        testimonials_page = PageContent(
            page_name='testimonials',
            title='Témoignages',
            subtitle='Ce que nos clients disent de nous.',
            body='''<p>Découvrez les avis de nos clients satisfaits.</p>
<p>Votre satisfaction est notre priorité !</p>'''
        )
        db.session.add(testimonials_page)

    partners_page = PageContent.query.filter_by(page_name='partners').first()
    if not partners_page:
        partners_page = PageContent(
            page_name='partners',
            title='Nos Partenaires',
            subtitle='Ensemble pour une agriculture durable.',
            body='''<p>Nous sommes fiers de travailler avec des partenaires engagés.</p>
<p>Découvrez ceux qui nous accompagnent dans notre démarche.</p>'''
        )
        db.session.add(partners_page)
    
    db.session.commit()
    click.echo("Création des pages de contenu terminée.")

@seed.command()
@with_appcontext
def reset():
    """Supprime TOUTES les données de toutes les tables, puis repeuple."""
    if not click.confirm(click.style('ATTENTION ! Ceci va supprimer TOUTES les données. Voulez-vous continuer ?', fg='red', bold=True)):
        return

    click.echo("Suppression de toutes les données...")

    # Désactiver temporairement les contraintes de clé étrangère (plus sûr et plus rapide)
    # Note: La syntaxe peut varier selon le SGBD (SQLite, PostgreSQL, MySQL)
    engine_name = db.engine.name
    if engine_name == 'mysql':
        db.session.execute('SET FOREIGN_KEY_CHECKS=0;')
    elif engine_name == 'postgresql':
        # Pour PostgreSQL, on pourrait utiliser TRUNCATE ... CASCADE, mais c'est plus complexe à gérer ici.
        # On va donc se fier à l'ordre de suppression manuel.
        pass

    # Suppression manuelle dans l'ordre inverse des dépendances
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())

    if engine_name == 'mysql':
        db.session.execute('SET FOREIGN_KEY_CHECKS=1;')

    db.session.commit()
    click.echo(click.style("Toutes les données ont été supprimées.", fg='green'))

    # On rappelle la commande de peuplement
    populate.callback()

@seed.command(name='full-reset')
@with_appcontext
def full_reset():
    """Supprime TOUTES les tables et les recrée (le plus radical)."""
    if not click.confirm(click.style('ATTENTION ! Ceci va supprimer TOUTES les tables et données. Voulez-vous continuer ?', fg='red', bold=True)):
        return

    click.echo("Suppression de toutes les tables de la base de données...")
    db.drop_all()
    db.session.commit()
    click.echo(click.style("Tables supprimées.", fg='green'))

    click.echo("Création de toutes les tables...")
    db.create_all()
    db.session.commit()
    click.echo(click.style("Tables créées.", fg='green'))

    # On rappelle la commande de peuplement
    populate.callback()
