# La Ferme Ousfa - Application E-commerce

Ce projet est une application web e-commerce complète et moderne, développée avec le framework Flask en Python. Elle est conçue pour gérer la vente de volaille et de produits maraîchers, en offrant une expérience utilisateur riche et un panneau d'administration puissant.

## Fonctionnalités

### Pour les Clients
- **Catalogue de Produits :** Navigation intuitive des produits par catégories avec recherche et filtrage.
- **Panier Intelligent :** Les articles ajoutés au panier sont **réservés pour une durée limitée**, garantissant leur disponibilité.
- **Recommandations de Produits :** Un système suggère des articles complémentaires en fonction du contenu du panier.
- **Avis sur les produits :** Possibilité de noter et de laisser un commentaire sur les produits.
- **Liste de souhaits (Wishlist) :** Les clients peuvent sauvegarder des produits pour les retrouver facilement plus tard, les consulter et les ajouter à leur panier.
- **Achat Intelligent :** Fonctionnalité permettant de définir un prix désiré sur un produit et d'être notifié lorsque celui-ci est atteint.
- **Espace Client :** Chaque client dispose d'un compte pour consulter son historique de commandes, gérer ses informations personnelles et son mot de passe.
- **Options de Paiement Flexibles :**
    - **Paiement Sécurisé en ligne :** Intégration complète avec Stripe.
    - **Paiement à la livraison :** Possibilité de payer la commande au moment de la réception.
- **Interaction et Contenu :**
    - **Formulaire de contact :** Pour poser des questions ou envoyer des messages.
    - **Inscription à la Newsletter :** Les visiteurs peuvent s'abonner pour recevoir les actualités et les promotions par e-mail.
    - **Pages d'information dynamiques :** Gérer le contenu de pages telles que la FAQ, les témoignages ou les partenaires via l'administration.

### Pour l'Administrateur
- **Tableau de Bord :** Une vue d'ensemble des ventes, des dernières commandes et des statistiques clés.
- **Gestion du Catalogue :** Interface complète pour gérer les produits, leurs images, les catégories et les stocks.
- **Gestion des Commandes Avancée :** Suivi détaillé des commandes via une grille de données interactive permettant :
    - La **pagination** pour naviguer facilement à travers un grand nombre de commandes.
    - Le **filtrage** par statut (En attente, Expédiée, etc.) et par plage de dates.
    - Le **tri** des commandes en cliquant sur les en-têtes de colonnes (ID, date, total, statut).
- **Gestion des Utilisateurs :** Administration des comptes clients et du personnel (admins, employés).
- **Gestion de Contenu :**
    - **Module de Blog :** Publier des actualités, des promotions ou des articles.
    - **Pages d'information dynamiques :** Gérer le contenu de pages telles que la FAQ, les témoignages ou les partenaires.
    - **Gestion des Abonnés Newsletter :** Consulter et gérer la liste des abonnés à la newsletter.
- **Communication :** Consulter et répondre aux messages envoyés via le formulaire de contact.

## Prérequis

- Python 3.8+
- pip (le gestionnaire de paquets de Python)
- virtualenv (recommandé)

## Installation

1.  **Cloner le projet** (si vous utilisez git) :
    ```bash
    git clone <url_du_repository>
    cd backend
    ```

2.  **Créer et activer un environnement virtuel** :
    ```bash
    # Créer l'environnement
    python -m venv venv

    # Activer l'environnement (sur Windows)
    .\venv\Scripts\activate
    ```

3.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurer les variables d'environnement** :
    Créez un fichier `.env` à la racine du projet et remplissez-le en vous basant sur ce modèle :
    ```ini
    SECRET_KEY='votre_super_cle_secrete_ici'
    EMAIL_USER='votre_adresse@gmail.com'
    EMAIL_PASS='votre_mot_de_passe_d_application_gmail'
    CLOUDINARY_CLOUD_NAME='votre_cloud_name_cloudinary'
    CLOUDINARY_API_KEY='votre_api_key_cloudinary'
    CLOUDINARY_API_SECRET='votre_api_secret_cloudinary'
    STRIPE_PUBLIC_KEY='pk_test_votre_cle_publique'
    STRIPE_SECRET_KEY='sk_test_votre_cle_secrete'
    STRIPE_ENDPOINT_SECRET='whsec_votre_secret_webhook'
    ```

## Utilisation

1.  **Initialiser la base de données** (pour la première fois) :
    ```bash
    flask create-db
    ```

2.  **Peupler la base de données** (Optionnel, pour ajouter des données de test) :
    ```bash
    flask seed
    ```

3.  **Créer un utilisateur Administrateur** :
    ```bash
    flask create-admin <nom_utilisateur> <email> <mot_de_passe>
    ```

4.  **Lancer l'application** :
    ```bash
    # En mode développement
    python app.py
    ```
    L'application sera accessible à l'adresse `http://127.0.0.1:5000`.

## Scripts Utilitaires

### Synchronisation de Répertoires (`sync_dirs.py`)

Un script utilitaire `sync_dirs.py` est inclus pour faciliter la sauvegarde ou la synchronisation de répertoires. Il effectue une synchronisation "miroir" unidirectionnelle d'un répertoire source vers un répertoire de destination.

**Fonctionnalités :**
- Copie les fichiers nouveaux ou modifiés de la source vers la destination.
- Supprime les fichiers de la destination qui n'existent plus dans la source.
- Affiche des barres de progression et le temps total de l'opération.

**Utilisation :**
```bash
python sync_dirs.py <chemin_source> <chemin_destination>
```

**Attention :** Ce script supprime des fichiers dans le répertoire de destination. À utiliser avec prudence.