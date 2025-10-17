from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db, bcrypt
from ..models import Customer, StaffUser, CartItem
from ..forms import LoginForm, RegistrationForm, PasswordResetRequestForm, ResetPasswordForm, ChangePasswordForm
from flask_mailman import EmailMessage

def send_reset_email(user):
    token = user.get_reset_token()
    subject = 'Demande de réinitialisation de mot de passe'
    body = f'''Pour réinitialiser votre mot de passe, veuillez visiter le lien suivant:
{url_for('auth.reset_token', token=token, _external=True)}

Si vous n\'avez pas fait cette demande, veuillez ignorer cet e-mail et aucun changement ne sera effectué.
'''
    msg = EmailMessage(subject,
                       body,
                       current_app.config['MAIL_DEFAULT_SENDER'],
                       [user.email])
    msg.send()

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        staff_user = StaffUser.query.filter_by(username=form.username.data).first()
        if staff_user and bcrypt.check_password_hash(staff_user.password, form.password.data):
            login_user(staff_user)
            flash('Connexion réussie en tant que personnel !', 'success')
            return redirect(url_for('admin.admin_dashboard'))

        customer_user = Customer.query.filter_by(username=form.username.data).first()
        if customer_user and bcrypt.check_password_hash(customer_user.password, form.password.data):
            login_user(customer_user)
            
            # Vider systématiquement le panier de l'utilisateur en base de données avant la fusion
            try:
                items_to_delete = CartItem.query.filter_by(customer_id=current_user.id).all()
                for item in items_to_delete:
                    db.session.delete(item)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erreur lors du vidage du panier pour le client {current_user.id} à la connexion: {e}")
                flash("Une erreur est survenue lors du nettoyage de votre panier.", "warning")

            # Logique de fusion du panier de session (si existant)
            if 'cart' in session:
                for product_id_str, quantity in session['cart'].items():
                    product_id = int(product_id_str)
                    # Après vidage, on peut ajouter directement sans vérifier l'existence
                    cart_item = CartItem(customer_id=current_user.id, product_id=product_id, quantity=quantity)
                    db.session.add(cart_item)
                db.session.commit()
                session.pop('cart', None)

            flash('Connexion réussie !', 'success')
            return redirect(url_for('main.index'))

        flash("Échec de la connexion. Veuillez vérifier votre nom d'utilisateur et votre mot de passe.", 'danger')

    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_customer = Customer(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_customer)
        db.session.commit()
        flash('Votre compte client a été créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))

@auth.route("/reset_password/", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = Customer.query.filter_by(email=form.email.data).first()
        if not user:
            user = StaffUser.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('Un e-mail a été envoyé avec les instructions pour réinitialiser votre mot de passe.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('reset_request.html', title='Réinitialiser le mot de passe', form=form)

@auth.route("/reset_password/<token>/", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = Customer.verify_reset_token(token)
    if not user:
        user = StaffUser.verify_reset_token(token)
    if user is None:
        flash('Ceci est un jeton invalide ou expiré', 'warning')
        return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(user.password, form.password.data):
            flash("Le nouveau mot de passe doit être différent de l'ancien.", 'danger')
            return render_template('reset_token.html', title='Réinitialiser le mot de passe', form=form, token=token)
            
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Votre mot de passe a été mis à jour ! Vous pouvez maintenant vous connecter', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_token.html', title='Réinitialiser le mot de passe', form=form, token=token)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data

        if not bcrypt.check_password_hash(current_user.password, old_password):
            flash("L'ancien mot de passe est incorrect.", 'danger')
        elif bcrypt.check_password_hash(current_user.password, new_password):
            flash("Le nouveau mot de passe doit être différent de l'actuel.", 'danger')
        elif current_user.previous_password and bcrypt.check_password_hash(current_user.previous_password, new_password):
            flash("Le nouveau mot de passe ne peut pas être identique au précédent.", 'danger')
        else:
            current_user.previous_password = current_user.password
            current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            flash('Votre mot de passe a été mis à jour avec succès !', 'success')
            return redirect(url_for('main.index'))

    return render_template('change_password.html', form=form)
