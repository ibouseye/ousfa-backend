from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required
from . import products
from .. import db
from ..models import Product, Category, Review, ReviewVote, Order, OrderItem, Customer, Banner
from ..forms import ReviewForm
from sqlalchemy import func, case

from datetime import datetime
from ..admin.routes import customer_required

@products.route('/produits')
def produits():
    """Affiche la liste de tous les produits avec pagination, filtre et tri."""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort_by', 'name_asc')

    products_query = db.select(Product)

    if search_query:
        products_query = products_query.join(Category).filter(
            (Product.name.ilike(f'%{search_query}%')) |
            (Category.name.ilike(f'%{search_query}%'))
        )

    if category_id:
        products_query = products_query.filter(Product.category_id == category_id)

    if sort_by == 'price_asc':
        products_query = products_query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        products_query = products_query.order_by(Product.price.desc())
    elif sort_by == 'name_desc':
        products_query = products_query.order_by(Product.name.desc())
    else: # name_asc is the default
        products_query = products_query.order_by(Product.name.asc())

    products_pagination = db.paginate(products_query, page=page, per_page=9)
    import logging
    logger = logging.getLogger(__name__)
    for product in products_pagination.items:
        logger.info(f"DEBUG (Produits): Product ID: {product.id}, Image File: {product.image_file}")
    categories = db.session.execute(db.select(Category)).scalars().all()

    # Récupérer les bannières pour la page produits
    product_page_banners = db.session.execute(Banner.get_active_banners().filter_by(position='product_page')).scalars().all()
    # Récupérer les bannières pour la barre latérale
    sidebar_banners = db.session.execute(Banner.get_active_banners().filter_by(position='sidebar')).scalars().all()

    return render_template('produits.html', 
                           products=products_pagination, 
                           search_query=search_query, 
                           categories=categories,
                           selected_category=category_id,
                           sort_by=sort_by,
                           product_page_banners=product_page_banners,
                           sidebar_banners=sidebar_banners)

@products.route('/produit/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    """Affiche la page de détail d'un produit spécifique."""
    product = db.session.get(Product, product_id)
    if not product:
        flash("Produit introuvable.", "danger")
        return redirect(url_for('products.produits'))

    form = ReviewForm()

    # Vérifier si l'utilisateur a acheté ce produit
    has_purchased = False
    if current_user.is_authenticated and isinstance(current_user, Customer): # Keep this check for has_purchased logic
        has_purchased = db.session.execute(db.select(Order).join(OrderItem).filter(
            Order.customer_id == current_user.id,
            OrderItem.product_id == product.id
        )).scalar_one_or_none() is not None

    if form.validate_on_submit() and has_purchased:
        review = Review(rating=form.rating.data, 
                        comment=form.comment.data, 
                        product_id=product.id, 
                        customer_id=current_user.id)
        db.session.add(review)
        db.session.commit()
        flash('Votre avis a été ajouté avec succès !', 'success')
        return redirect(url_for('products.product_detail', product_id=product.id))

    # Calcul de la note moyenne
    avg_rating = db.session.execute(db.select(db.func.avg(Review.rating)).filter(Review.product_id == product.id)).scalar_one_or_none() or 0

    # Fetch reviews and their vote counts (optimized)
    reviews_with_votes = []
    
    reviews = db.session.execute(db.select(Review).filter(Review.product_id == product.id)).scalars().all()

    if reviews:
        review_ids = [r.id for r in reviews]

        votes = db.session.query(
            ReviewVote.review_id,
            func.count(case((ReviewVote.vote_type == 'useful', 1))).label('useful_count'),
            func.count(case((ReviewVote.vote_type == 'not_useful', 1))).label('not_useful_count')
        ).filter(ReviewVote.review_id.in_(review_ids)).group_by(ReviewVote.review_id).all()
        
        votes_by_review = {r_id: {'useful': u_count, 'not_useful': nu_count} for r_id, u_count, nu_count in votes}

        user_votes = {}
        if current_user.is_authenticated and isinstance(current_user, Customer):
            user_vote_list = db.session.execute(db.select(ReviewVote).filter(
                ReviewVote.review_id.in_(review_ids),
                ReviewVote.customer_id == current_user.id
            )).scalars().all()
            user_votes = {v.review_id: v.vote_type for v in user_vote_list}

        for review in reviews:
            vote_counts = votes_by_review.get(review.id, {'useful': 0, 'not_useful': 0})
            reviews_with_votes.append({
                'review': review,
                'useful_count': vote_counts['useful'],
                'not_useful_count': vote_counts['not_useful'],
                'user_vote': user_votes.get(review.id)
            })

    # Récupérer les bannières pour la page de détail du produit
    product_page_banners = db.session.execute(Banner.get_active_banners().filter_by(position='product_page')).scalars().all()

    return render_template('product_detail.html', 
                           product=product, 
                           form=form, 
                           has_purchased=has_purchased,
                           avg_rating=avg_rating,
                           reviews_with_votes=reviews_with_votes,
                           product_page_banners=product_page_banners)

@products.route('/review/<int:review_id>/vote', methods=['POST'])
@login_required
@customer_required
def vote_review(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        return jsonify({'success': False, 'message': 'Avis introuvable.'}), 404

    

    if review.customer_id == current_user.id:
        return jsonify({'success': False, 'message': 'Vous ne pouvez pas voter sur votre propre avis.'}), 403

    data = request.get_json()
    vote_type = data.get('vote_type')

    if vote_type not in ['useful', 'not_useful']:
        return jsonify({'success': False, 'message': 'Type de vote invalide.'}), 400

    existing_vote = db.session.execute(db.select(ReviewVote).filter_by(
        review_id=review_id,
        customer_id=current_user.id
    )).scalar_one_or_none()

    try:
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                db.session.delete(existing_vote)
                message = 'Votre vote a été retiré.'
            else:
                existing_vote.vote_type = vote_type
                message = 'Votre vote a été mis à jour.'
        else:
            new_vote = ReviewVote(
                review_id=review_id,
                customer_id=current_user.id,
                vote_type=vote_type
            )
            db.session.add(new_vote)
            message = 'Votre vote a été enregistré.'
        
        db.session.commit()

        useful_count = db.session.query(func.count(ReviewVote.id)).filter_by(review_id=review_id, vote_type='useful').scalar()
        not_useful_count = db.session.query(func.count(ReviewVote.id)).filter_by(review_id=review_id, vote_type='not_useful').scalar()

        return jsonify({
            'success': True,
            'message': message,
            'useful_count': useful_count,
            'not_useful_count': not_useful_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur lors de l\'enregistrement du vote: {e}'}), 500
