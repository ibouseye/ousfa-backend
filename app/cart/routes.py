from flask import render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_required, current_user
from . import cart
from .. import db
from ..models import Product, Order, OrderItem, Customer, CartItem, Milestone
from ..forms import CheckoutForm
from ..admin.routes import customer_required
from flask_mailman import EmailMessage
from ..utils.stock_helpers import check_and_update_stock
from ..utils.recommendations import get_product_recommendations # NOUVELLE IMPORTATION
import stripe
from sqlalchemy import func

# NOUVELLES IMPORTATIONS pour la réservation
from datetime import datetime, timedelta, timezone

# Constante pour la durée de réservation (en minutes)
RESERVATION_DURATION_MINUTES = 15 # Vous pouvez ajuster cette valeur

@cart.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)

    if product_id and quantity and quantity > 0:
        # Get the product to pass to the helper function
        product = db.session.get(Product, product_id)
        if not product:
            flash('Produit introuvable.', 'danger')
            return redirect(url_for('products.produits')) # Keep this redirect for product not found

        current_cart_quantity = 0
        if current_user.is_authenticated and isinstance(current_user, Customer):
            cart_item = db.session.execute(db.select(CartItem).filter_by(customer_id=current_user.id, product_id=product_id)).scalar_one_or_none()
            if cart_item:
                current_cart_quantity = cart_item.quantity
        else:
            if 'cart' in session:
                current_cart_quantity = session['cart'].get(str(product_id), 0)

        is_sufficient_stock, message = check_and_update_stock(product_id, quantity, current_cart_quantity)

        if not is_sufficient_stock:
            flash(message, 'danger')
            return redirect(url_for('products.product_detail', product_id=product_id)) # Redirect to product detail page

        if current_user.is_authenticated and isinstance(current_user, Customer):
            if cart_item:
                cart_item.quantity += quantity
                # Mettre à jour la date de réservation si l'article existe déjà
                cart_item.reserved_until = datetime.now(timezone.utc) + timedelta(minutes=RESERVATION_DURATION_MINUTES)
            else:
                # Créer un nouvel article de panier avec la date de réservation
                cart_item = CartItem(
                    customer_id=current_user.id,
                    product_id=product_id,
                    quantity=quantity,
                    reserved_until=datetime.now(timezone.utc) + timedelta(minutes=RESERVATION_DURATION_MINUTES) # Définir la date de réservation
                )
                db.session.add(cart_item)
            db.session.commit()
            flash(message, 'success') # Use message from helper function
        else:
            # Pour les utilisateurs non connectés, la réservation est gérée par la session
            if 'cart' not in session:
                session['cart'] = {}
            
            session['cart'][str(product_id)] = current_cart_quantity + quantity
            session.modified = True
            flash(message, 'success') # Use message from helper function
    else:
        flash('Quantité invalide ou produit manquant.', 'danger')
        # If product_id is missing, we can't redirect to product_detail, so redirect to produits
        return redirect(url_for('products.produits'))

    return redirect(url_for('products.produits')) # Default redirect if no specific error

@cart.route('/cart')
def cart_view():
    cart_items_list = []
    total_price = 0
    current_cart_product_ids = [] # Pour collecter les IDs des produits dans le panier
    
    if current_user.is_authenticated and isinstance(current_user, Customer):
        cart_items = db.session.execute(db.select(CartItem).filter_by(customer_id=current_user.id)).scalars().all()
        for item in cart_items:
            item_total = item.product.price * item.quantity
            total_price += item_total
            cart_items_list.append({
                'product': item.product,
                'quantity': item.quantity,
                'item_total': item_total
            })
            current_cart_product_ids.append(item.product.id) # Ajouter l'ID du produit
    else:
        if 'cart' in session and session['cart']:
            for product_id_str, quantity in session['cart'].items():
                product = db.session.get(Product, int(product_id_str))
                if product:
                    item_total = product.price * quantity
                    total_price += item_total
                    cart_items_list.append({
                        'product': product,
                        'quantity': quantity,
                        'item_total': item_total
                    })
                    current_cart_product_ids.append(product.id) # Ajouter l'ID du produit
    
    # Obtenir les recommandations
    recommended_products = []
    if current_cart_product_ids: # Ne chercher des recommandations que si le panier n'est pas vide
        recommended_products = get_product_recommendations(current_cart_product_ids)

    return render_template('cart.html', cart_items=cart_items_list, total_price=total_price, recommended_products=recommended_products) # Passer les recommandations au template

@cart.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id', type=int)
    action = request.form.get('action')
    quantity = request.form.get('quantity', type=int)
    
    message = None
    category = 'info'

    if current_user.is_authenticated and isinstance(current_user, Customer):
        cart_item = db.session.execute(db.select(CartItem).filter_by(customer_id=current_user.id, product_id=product_id)).scalar_one_or_none()
        if cart_item:
            if action == 'set' and quantity is not None and quantity >= 0:
                if quantity == 0:
                    db.session.delete(cart_item)
                    message = 'Produit retiré du panier.'
                else:
                    cart_item.quantity = quantity
                    message = 'Quantité mise à jour.'
                    category = 'success'
            elif action == 'remove':
                db.session.delete(cart_item)
                message = 'Produit retiré du panier.'
            else:
                message = 'Action ou quantité invalide.'
                category = 'danger'
            db.session.commit()
        else:
            message = 'Produit non trouvé dans le panier.'
            category = 'danger'
    else:
        if 'cart' in session and session['cart'] and product_id:
            product_id_str = str(product_id)
            if action == 'set' and quantity is not None and quantity >= 0:
                if quantity == 0:
                    session['cart'].pop(product_id_str, None)
                    message = 'Produit retiré du panier.'
                else:
                    session['cart'][product_id_str] = quantity
                    message = 'Quantité mise à jour.'
                    category = 'success'
            elif action == 'remove':
                session['cart'].pop(product_id_str, None)
                message = 'Produit retiré du panier.'
            else:
                message = 'Action ou quantité invalide.'
                category = 'danger'
            session.modified = True
        else:
            message = 'Panier vide ou produit manquant.'
            category = 'danger'
    
    if message:
        flash(message, category)
    
    return redirect(url_for('cart.cart_view'))

@cart.route('/checkout', methods=['GET', 'POST'])
@login_required
@customer_required
def checkout():
    cart_items_list = []
    total_order_price = 0
    
    cart_items = db.session.execute(db.select(CartItem).filter_by(customer_id=current_user.id)).scalars().all()
    if not cart_items:
        flash('Votre panier est vide.', 'warning')
        return redirect(url_for('products.produits'))
    
    # --- DÉBUT DE LA LOGIQUE DE VÉRIFICATION DE RÉSERVATION ---
    expired_items_removed = False
    items_to_remove_from_cart = []
    expired_product_names = [] # Nouvelle liste pour stocker les noms des produits expirés

    for item in cart_items:
        # Vérifier si l'article a une date de réservation et si elle est expirée
        if item.reserved_until and datetime.now(timezone.utc) > item.reserved_until.replace(tzinfo=timezone.utc):
            expired_product_names.append(item.product.name) # Ajouter le nom du produit
            items_to_remove_from_cart.append(item)
            expired_items_removed = True
        else:
            item_total = item.product.price * item.quantity
            total_order_price += item_total
            cart_items_list.append({
                'product': item.product,
                'quantity': item.quantity,
                'item_total': item_total,
                'reserved_until': item.reserved_until # Passer la date de réservation au template si besoin
            })
    
    # Supprimer les articles expirés de la base de données
    for item in items_to_remove_from_cart:
        db.session.delete(item)
    
    if expired_items_removed:
        db.session.commit() # Committer les suppressions
        # Si des articles ont été retirés, afficher un seul message
        if expired_product_names:
            flash(f'La réservation pour les articles suivants a expiré et ils ont été retirés de votre panier : {", ".join(expired_product_names)}.', 'warning')
        # Rediriger vers le panier pour que l'utilisateur voie les changements
        return redirect(url_for('cart.cart_view'))

    # Si le panier est vide après la suppression des articles expirés
    if not cart_items_list:
        flash("Votre panier est vide après l'expiration de certaines réservations.", 'warning')
        return redirect(url_for('products.produits'))
    # --- FIN DE LA LOGIQUE DE VÉRIFICATION DE RÉSERVATION ---

    errors = []
    checkout_form = CheckoutForm()

    for item in cart_items_list:
        product = item['product']
        quantity = item['quantity']
        if product.stock < quantity:
            errors.append(f"La quantité demandée pour {product.name} ({quantity}) dépasse le stock disponible ({product.stock}).")

    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('cart.cart_view'))

    # --- LOGIQUE DE LA COMMANDE GAGNANTE (GET) ---
    is_milestone_order = False
    next_milestone = None
    milestone_orders_db = db.session.execute(db.select(Milestone).order_by(Milestone.order_number.asc())).scalars().all()
    milestone_numbers = [m.order_number for m in milestone_orders_db]
    
    # On compte les commandes qui sont considérées comme "finalisées"
    completed_orders_count = db.session.query(func.count(Order.id)).filter(Order.status.in_([
        'Paiement à la livraison',
        'Payée',
        'En cours de traitement',
        'Expédiée',
        'Terminée'
    ])).scalar()
    
    next_order_number = completed_orders_count + 1
    if next_order_number in milestone_numbers:
        is_milestone_order = True
        next_milestone = next_order_number
    # --- FIN DE LA LOGIQUE ---

    if checkout_form.validate_on_submit():
        payment_method = checkout_form.payment_method.data
        if payment_method == 'cod':
            try:
                final_stock_errors = []
                for item in cart_items_list:
                    product = db.session.get(Product, item['product'].id)
                    if not product or product.stock < item['quantity']:
                        final_stock_errors.append(f"Le stock pour {item['product'].name} est insuffisant. Disponible: {product.stock if product else 0}, Demandé: {item['quantity']}.")
                
                if final_stock_errors:
                    db.session.rollback()
                    for error in final_stock_errors:
                        flash(error, 'danger')
                    return redirect(url_for('cart.cart_view'))

                new_order = Order(
                    customer_id=current_user.id,
                    total_price=total_order_price,
                    status='Paiement à la livraison'
                )
                db.session.add(new_order)
                db.session.flush()

                for item in cart_items_list:
                    product = db.session.get(Product, item['product'].id)
                    product.stock -= item['quantity']
                    order_item = OrderItem(
                        order_id=new_order.id,
                        product_id=product.id,
                        quantity=item['quantity'],
                        price_at_purchase=product.price
                    )
                    db.session.add(order_item)
                
                # Vider le panier de manière explicite
                items_to_delete = CartItem.query.filter_by(customer_id=current_user.id).all()
                for item in items_to_delete:
                    db.session.delete(item)

                if new_order.id in milestone_numbers:
                    new_order.is_milestone = True
                
                db.session.commit()

                try:
                    subject = f"Confirmation de votre commande #{new_order.id}"
                    html_body = render_template('order_confirmation.html', order=new_order)
                    text_content = "Veuillez activer l'affichage HTML pour voir le contenu de cet e-mail."
                    msg = EmailMessage(subject=subject,
                                       body=html_body, # HTML content as body
                                       from_email=current_app.config['MAIL_DEFAULT_SENDER'],
                                       to=[new_order.customer.email])
                    msg.content_subtype = "html" # Explicitly set content type
                    msg.alt_body = text_content # Add plain text alternative
                    msg.send()
                except Exception as e:
                    current_app.logger.error(f"Error sending email for order {new_order.id}: {e}") # Ajout du logging
                    flash(f"Votre commande a été enregistrée, mais l'envoi de l'e-mail de confirmation a échoué : {e}", "warning")

                # --- LOGIQUE DE LA COMMANDE GAGNANTE (POST) ---
                if new_order.is_milestone:
                    flash(f'Félicitations ! Vous êtes notre client n°{new_order.id} ! Un cadeau surprise sera ajouté à votre commande.', 'milestone-win')
                else:
                    flash('Votre commande a été passée avec succès ! Vous paierez à la livraison.', 'success')
                # --- FIN DE LA LOGIQUE ---
                return redirect(url_for('main.my_orders'))

            except Exception as e:
                db.session.rollback()
                flash(f"Une erreur est survenue lors de la création de votre commande : {e}", "danger")
                return redirect(url_for('cart.checkout'))
        
        elif payment_method == 'stripe':
            # Vérification du montant minimum pour Stripe
            MIN_AMOUNT_XOF = 330  # Correspond à environ 0.50 EUR
            if total_order_price < MIN_AMOUNT_XOF:
                flash(f'Le montant total de la commande doit être d\'au moins {MIN_AMOUNT_XOF} XOF pour un paiement par carte.', 'danger')
                return redirect(url_for('cart.cart_view'))

            try:
                # Supprimer les anciennes commandes en attente pour éviter les doublons
                existing_pending_orders = db.session.execute(db.select(Order).filter_by(customer_id=current_user.id, status='En attente de paiement')).scalars().all()
                if existing_pending_orders:
                    for old_order in existing_pending_orders:
                        db.session.query(OrderItem).filter_by(order_id=old_order.id).delete()
                        db.session.delete(old_order)
                    db.session.commit()

                # Create a new order with status 'En attente de paiement'
                new_order = Order(
                    customer_id=current_user.id,
                    total_price=total_order_price,
                    status='En attente de paiement'
                )
                db.session.add(new_order)
                db.session.flush()

                if new_order.id in milestone_numbers:
                    new_order.is_milestone = True

                for item in cart_items_list:
                    product = db.session.get(Product, item['product'].id)
                    order_item = OrderItem(
                        order_id=new_order.id,
                        product_id=product.id,
                        quantity=item['quantity'],
                        price_at_purchase=product.price
                    )
                    db.session.add(order_item)
                
                db.session.commit()

                stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
                line_items = []
                for item in cart_items_list:
                    line_items.append({
                        'price_data': {
                            'currency': 'xof',
                            'product_data': {
                                'name': item['product'].name,
                            },
                            'unit_amount': int(item['product'].price),
                        },
                        'quantity': item['quantity'],
                    })
                
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=line_items,
                    mode='payment',
                    success_url=url_for('cart.success', order_id=new_order.id, _external=True),
                    cancel_url=url_for('cart.cancel', _external=True),
                    metadata={'order_id': new_order.id}
                )
                return redirect(checkout_session.url, code=303)
            except Exception as e:
                db.session.rollback()
                flash(f'Erreur lors de la création de la session de paiement : {e}', 'danger')
                return redirect(url_for('cart.checkout'))

    return render_template('checkout.html', cart_items=cart_items_list, total_order_price=total_order_price, checkout_form=checkout_form, is_milestone_order=is_milestone_order, next_milestone=next_milestone)

@cart.route('/success')
@login_required
def success():
    order_id = request.args.get('order_id', type=int)
    if not order_id:
        flash('ID de commande manquant.', 'danger')
        return redirect(url_for('main.index'))
        
    order = db.session.get(Order, order_id)
    
    if not order or order.customer_id != current_user.id:
        flash('Commande non trouvée ou accès non autorisé.', 'danger')
        return redirect(url_for('main.index'))
        
    try:
        # Logique de finalisation de la commande déplacée ici
        if order.status == 'En attente de paiement':
            order.status = 'Payée'
            
            # Décrémenter le stock
            for item in order.items:
                product = db.session.get(Product, item.product_id)
                if product.stock < item.quantity:
                    flash(f'Erreur: le stock pour {product.name} est devenu insuffisant.', 'danger')
                    db.session.rollback()
                    return redirect(url_for('cart.cart_view'))
                product.stock -= item.quantity

            # Envoyer l'email de confirmation
            try:
                subject = f"Confirmation de votre commande #{order.id}"
                html_body = render_template('order_confirmation.html', order=order)
                text_content = "Veuillez activer l'affichage HTML pour voir le contenu de cet e-mail."
                msg = EmailMessage(subject=subject,
                                   body=html_body, # HTML content as body
                                   from_email=current_app.config['MAIL_DEFAULT_SENDER'],
                                   to=[order.customer.email])
                msg.content_subtype = "html" # Explicitly set content type
                msg.alt_body = text_content # Add plain text alternative
                msg.send()
            except Exception as e:
                current_app.logger.error(f"Error sending email for order {order.id}: {e}")
                flash("Votre commande est confirmée, mais l'envoi de l'e-mail a échoué.", "warning")

        # Vider le panier (logique existante)
        items_to_delete = db.session.execute(db.select(CartItem).filter_by(customer_id=current_user.id)).scalars().all()
        for item in items_to_delete:
            db.session.delete(item)
        
        db.session.commit()

        # --- LOGIQUE DE LA COMMANDE GAGNANTE (Stripe) ---
        if order.is_milestone:
            flash(f'Félicitations ! Vous êtes notre client n°{order.id} ! Un cadeau surprise sera ajouté à votre commande.', 'milestone-win')
        # --- FIN DE LA LOGIQUE ---

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la finalisation de la commande {order_id}: {e}")
        flash('Une erreur est survenue lors de la finalisation de votre commande.', 'danger')
        return redirect(url_for('cart.cart_view'))

    return render_template('success.html', order=order)

@cart.route('/cancel')
def cancel():
    return render_template('cancel.html')

@cart.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = current_app.config.get('STRIPE_ENDPOINT_SECRET')
    
    if not endpoint_secret:
        current_app.logger.error('Stripe endpoint secret not configured')
        return 'Stripe endpoint secret not configured', 500

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        current_app.logger.error(f'Invalid payload: {e}')
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        current_app.logger.error(f'Invalid signature: {e}')
        return 'Invalid signature', 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('metadata', {}).get('order_id')
        
        if not order_id:
            current_app.logger.error('Missing order_id in Stripe session metadata')
            return 'Missing order_id', 400
            
        order = db.session.get(Order, order_id)
        
        if not order:
            current_app.logger.error(f'Order not found for order_id: {order_id}')
            return 'Order not found', 404
            
        if order.status != 'En attente de paiement':
            current_app.logger.warning(f'Order {order_id} already processed')
            return 'Order already processed', 200
            
        try:
            order.status = 'Payée'
            
            # Decrease stock
            for item in order.items:
                product = db.session.get(Product, item.product_id)
                if product.stock < item.quantity:
                    raise Exception(f'Not enough stock for product {product.name}')
                product.stock -= item.quantity
            
            # Clear the cart
            items_to_delete = db.session.execute(db.select(CartItem).filter_by(customer_id=order.customer_id)).scalars().all()
            for item in items_to_delete:
                db.session.delete(item)
            
            db.session.commit()
            
            # Send confirmation email
            try:
                subject = f"Confirmation de votre commande #{order.id}"
                html_body = render_template('order_confirmation.html', order=order)
                text_content = "Veuillez activer l'affichage HTML pour voir le contenu de cet e-mail."
                msg = EmailMessage(subject=subject,
                                   body=text_content,
                                   from_email=current_app.config['MAIL_DEFAULT_SENDER'],
                                   to=[order.customer.email],
                                   html=html_body)
                msg.send()
            except Exception as e:
                current_app.logger.error(f"Error sending email for order {order.id}: {e}")
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing order {order_id}: {e}")
            return 'Error processing order', 500

    return 'Success', 200