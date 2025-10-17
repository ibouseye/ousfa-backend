from flask import render_template, request, flash, redirect, url_for
from datetime import datetime
from flask_login import login_required, current_user
from . import main
from .. import db
from ..models import Product, ContactMessage, Order, Customer, StaffUser, Post, PageContent, Banner, NewsletterSubscriber
from ..forms import ContactForm, ProfileForm, NewsletterForm
from ..admin.routes import customer_required
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse, parse_qs

@main.route('/')
def index():
    """Cette fonction est appelée lorsque quelqu'un visite la page d'accueil."""
    latest_products = db.session.execute(db.select(Product).order_by(Product.id.desc()).limit(3)).scalars().all()
    
    # Récupérer les bannières pour la page d'accueil
    homepage_banners = db.session.execute(Banner.get_active_banners().filter_by(position='homepage')).scalars().all()
    
    return render_template('index.html', latest_products=latest_products, homepage_banners=homepage_banners)

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    """Affiche le formulaire de contact et gère sa soumission."""
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        message = form.message.data
        new_contact_message = ContactMessage(name=name, email=email, message=message)
        try:
            db.session.add(new_contact_message)
            db.session.commit()
            flash('Votre message a été envoyé avec succès ! Nous vous recontacterons bientôt.', 'success')
            return redirect(url_for('main.contact'))
        except IntegrityError:
            db.session.rollback()
            flash('Il semble que vous nous ayez déjà contactés avec cette adresse e-mail. Nous avons bien reçu votre message !', 'warning')
            return redirect(url_for('main.contact'))
        except Exception as e:
            db.session.rollback()
            flash("Une erreur inattendue est survenue. Veuillez réessayer plus tard.", 'danger')
            return redirect(url_for('main.contact'))
    return render_template('contact.html', form=form)

@main.route('/profil', methods=['GET', 'POST'])
@login_required
@customer_required
def profile():
    form = ProfileForm(original_username=current_user.username, original_email=current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Votre profil a été mis à jour avec succès.", "success")
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('profile.html', form=form)

@main.route('/mes-commandes')
@login_required
@customer_required
def my_orders():
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.date_ordered.desc()).all()
    return render_template('my_orders.html', orders=orders)

@main.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if not (isinstance(current_user, StaffUser) and current_user.is_admin) and order.customer_id != current_user.id:
        flash("Vous n'avez pas l'autorisation de voir cette commande.", "danger")
        return redirect(url_for('main.index'))
    return render_template('order_detail.html', order=order)

@main.route('/realisations')
def realisations():
    """Affiche la page des réalisations."""
    posts = db.session.execute(db.select(Post).order_by(Post.created_at.desc())).scalars().all()
    return render_template('realisations.html', posts=posts)

@main.route('/realisations/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    embed_url = None
    if post.video_url:
        try:
            video_id = None
            parsed_url = urlparse(post.video_url)
            if 'youtube.com' in parsed_url.netloc:
                if 'watch' in parsed_url.path:
                    video_id = parse_qs(parsed_url.query).get('v', [None])[0]
                elif '/shorts/' in parsed_url.path:
                    video_id = parsed_url.path.split('/shorts/')[1]
            elif 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')
            
            if video_id:
                embed_url = f'https://www.youtube.com/embed/{video_id}'
        except Exception:
            embed_url = None
    return render_template('post_detail.html', post=post, embed_url=embed_url)

# The /about route is now handled by the generic dynamic_page route

@main.route('/subscribe_newsletter', methods=['POST'])
def subscribe_newsletter():
    form = NewsletterForm()
    if form.validate_on_submit():
        email = form.email.data
        try:
            subscriber = NewsletterSubscriber(email=email)
            db.session.add(subscriber)
            db.session.commit()
            flash('Merci de vous être abonné à notre newsletter !', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Cette adresse e-mail est déjà abonnée à notre newsletter.', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors de l'abonnement : {e}", 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur pour le champ {getattr(form, field).label.text}: {error}", 'danger')
    
    # Redirect back to the page where the form was submitted
    return redirect(request.referrer or url_for('main.index'))

@main.route('/page/<string:page_name>')
def dynamic_page(page_name):
    content = db.session.get(PageContent, page_name)
    if not content:
        flash("Page non trouvée.", "danger")
        return redirect(url_for('main.index'))
    return render_template('dynamic_page.html', content=content)