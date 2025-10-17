# -*- coding: utf-8 -*-

# Ce script est un "seeder", il sert à peupler notre base de données avec des données initiales.
# C'est très pratique pour tester l'application sans avoir à tout rentrer à la main.

# On importe la fonction create_app et l'objet db
from app import create_app, db
from app.models import Product, Category

# On crée une instance de l'application
app = create_app()

# --- Le script de peuplement ---

# On s'assure que ce script s'exécute dans le bon "contexte" d'application Flask.
# C'est nécessaire pour que SQLAlchemy sache à quelle base de données se connecter.
with app.app_context():
    print("Suppression des anciens produits et catégories...")
    # Pour éviter les doublons à chaque exécution, on supprime tous les produits et catégories existants.
    Product.query.delete()
    Category.query.delete()
    db.session.commit()

    print("Création des nouvelles catégories...")
    cat_volaille = Category(name='Volaille')
    cat_maraichage = Category(name='Maraîchage')
    db.session.add(cat_volaille)
    db.session.add(cat_maraichage)
    db.session.commit()

    print("Création des nouveaux produits...")
    # On crée une liste d'objets Product
    products = [
        Product(
            name='Poulet de chair',
            category=cat_volaille,
            description='Élevé en plein air, notre poulet de chair est tendre et savoureux.',
            price=5000,
            image_file='poulet.jpg'
        ),
        Product(
            name='Pintade',
            category=cat_volaille,
            description='Une viande fine et goûteuse, parfaite pour les repas de fête.',
            price=7000,
            image_file='pintade.jpg'
        ),
        Product(
            name='Oeufs de poule',
            category=cat_volaille,
            description='Des oeufs frais du jour, au jaune riche et crémeux.',
            price=1500,
            image_file='oeufs.jpg'
        ),
        Product(
            name='Tomate',
            category=cat_maraichage,
            description='Nos tomates sont cultivées en plein champ et cueillies à maturité.',
            price=1000,
            image_file='tomate.jpg'
        ),
        Product(
            name='Oignon vert',
            category=cat_maraichage,
            description='Idéal pour relever vos salades et plats cuisinés.',
            price=500,
            image_file='oignon.jpg'
        )
    ]

    # On ajoute tous les produits de notre liste à la "session" de la base de données.
    # La session est une zone de transit avant l'écriture finale.
    db.session.add_all(products)

    # On valide la transaction. C'est à ce moment que les données sont réellement écrites
    # dans le fichier site.db.
    db.session.commit()

    print("Les produits ont été ajoutés avec succès !")