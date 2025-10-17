from .. import db
from ..models import Product, OrderItem
from sqlalchemy import func

def get_product_recommendations(current_cart_product_ids, limit=4):
    # Convertir les IDs en entiers pour s'assurer de la compatibilité
    current_cart_product_ids = [int(pid) for pid in current_cart_product_ids]

    # Subquery pour trouver les order_ids qui contiennent les produits du panier actuel
    relevant_order_ids = db.session.query(OrderItem.order_id).filter(
        OrderItem.product_id.in_(current_cart_product_ids)
    ).distinct().subquery()

    # Trouver tous les autres produits dans ces commandes pertinentes
    recommended_product_ids = db.session.query(
        OrderItem.product_id,
        func.count(OrderItem.product_id).label('count')
    ).filter(
        OrderItem.order_id.in_(db.session.query(relevant_order_ids)),
        ~OrderItem.product_id.in_(current_cart_product_ids) # Exclure les produits déjà dans le panier
    ).group_by(OrderItem.product_id).order_by(func.count(OrderItem.product_id).desc()).limit(limit).all()

    # Récupérer les objets Product pour les IDs recommandés
    recommendations = []
    for product_id, count in recommended_product_ids:
        product = db.session.get(Product, product_id)
        if product:
            recommendations.append(product)
    
    return recommendations
