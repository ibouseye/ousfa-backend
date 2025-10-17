from .. import db
from ..models import Product

def check_and_update_stock(product_id, quantity_to_add, current_cart_quantity):
    product = db.session.get(Product, product_id)
    if not product:
        return False, 'Produit introuvable.'

    if product.stock == 0:
        return False, f'Désolé, {product.name} est en rupture de stock.'

    total_quantity_in_cart = current_cart_quantity + quantity_to_add

    if total_quantity_in_cart > product.stock:
        available_to_add = product.stock - current_cart_quantity
        if available_to_add > 0:
            return False, f'Vous ne pouvez pas ajouter {quantity_to_add} x {product.name}. Seulement {available_to_add} disponible(s) en stock.'
        else:
            return False, f'Vous avez déjà la quantité maximale de {product.name} disponible en stock.'
    
    return True, f'{quantity_to_add} x {product.name} ajouté(s) au panier !'