from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from . import wishlist
from .. import db
from ..models import Product, Customer, WishlistItem, CartItem
from ..admin.routes import customer_required
from sqlalchemy.exc import IntegrityError

@wishlist.route('/')
@login_required
@customer_required
def view_wishlist():
    wishlist_items = db.session.execute(db.select(WishlistItem).filter_by(customer_id=current_user.id)).scalars().all()
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@wishlist.route('/add/<int:product_id>', methods=['POST'])
@login_required
@customer_required
def add_to_wishlist(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Produit introuvable.", "danger")
        return redirect(url_for('products.produits'))

    try:
        wishlist_item = WishlistItem(customer_id=current_user.id, product_id=product.id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash(f"'{product.name}' a été ajouté à votre liste de souhaits.", "success")
    except IntegrityError:
        db.session.rollback()
        flash(f"'{product.name}' est déjà dans votre liste de souhaits.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur est survenue lors de l'ajout à la liste de souhaits : {e}", "danger")

    return redirect(url_for('products.product_detail', product_id=product.id))

@wishlist.route('/remove/<int:item_id>', methods=['POST'])
@login_required
@customer_required
def remove_from_wishlist(item_id):
    wishlist_item = db.session.get(WishlistItem, item_id)
    if not wishlist_item or wishlist_item.customer_id != current_user.id:
        flash("Article de la liste de souhaits introuvable ou non autorisé.", "danger")
        return redirect(url_for('wishlist.view_wishlist'))

    try:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash(f"'{wishlist_item.product.name}' a été retiré de votre liste de souhaits.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur est survenue lors du retrait de la liste de souhaits : {e}", "danger")

    return redirect(url_for('wishlist.view_wishlist'))

@wishlist.route('/move_to_cart/<int:item_id>', methods=['POST'])
@login_required
@customer_required
def move_to_cart_from_wishlist(item_id):
    wishlist_item = db.session.get(WishlistItem, item_id)
    if not wishlist_item or wishlist_item.customer_id != current_user.id:
        flash("Article de la liste de souhaits introuvable ou non autorisé.", "danger")
        return redirect(url_for('wishlist.view_wishlist'))

    product = wishlist_item.product
    if product.stock < 1: # Assuming moving one item
        flash(f"'{product.name}' est en rupture de stock et ne peut pas être ajouté au panier.", "danger")
        return redirect(url_for('wishlist.view_wishlist'))

    try:
        # Add to cart
        cart_item = db.session.execute(db.select(CartItem).filter_by(customer_id=current_user.id, product_id=product.id)).scalar_one_or_none()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(customer_id=current_user.id, product_id=product.id, quantity=1)
            db.session.add(cart_item)
        
        # Remove from wishlist
        db.session.delete(wishlist_item)
        db.session.commit()
        flash(f"'{product.name}' a été déplacé de votre liste de souhaits vers votre panier.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur est survenue lors du déplacement vers le panier : {e}", "danger")

    return redirect(url_for('cart.cart_view'))