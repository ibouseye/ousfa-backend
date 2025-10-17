from flask import current_app
import re
from typing import Optional
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, SubmitField, TextAreaField, FloatField, IntegerField, HiddenField, MultipleFileField, RadioField, URLField, DateField, BooleanField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from flask_wtf.file import FileAllowed, FileField
from .models import Customer, StaffUser, Milestone, NewsletterSubscriber, Newsletter
from app.extensions import db

def validate_password_strength(form, field):
    password = field.data
    if password:
        if not re.search(r'[a-z]', password):
            raise ValidationError('Le mot de passe doit contenir au moins une lettre minuscule.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Le mot de passe doit contenir au moins une lettre majuscule.')
        if not re.search(r'\d', password):
            raise ValidationError('Le mot de passe doit contenir au moins un chiffre.')

class MilestoneForm(FlaskForm):
    order_number = IntegerField('Numéro de Commande', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Ajouter le Palier')

    def validate_order_number(self, order_number):
        milestone = db.session.execute(db.select(Milestone).filter_by(order_number=order_number.data)).scalar_one_or_none()
        if milestone:
            raise ValidationError('Ce palier existe déjà.')

class BannerForm(FlaskForm):
    title = StringField('Titre de la bannière', validators=[DataRequired(), Length(min=2, max=100)])
    message = TextAreaField('Message de la bannière', validators=[Optional(), Length(max=500)])
    image = FileField('Image de la bannière', validators=[FileAllowed(['jpg', 'png', 'webp'], 'Images seulement!'), Optional()])
    link_url = StringField('URL du lien (optionnel)', validators=[Optional(), Length(max=200)])
    is_active = BooleanField('Bannière active')
    start_date = DateField('Date de début (optionnel)', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('Date de fin (optionnel)', format='%Y-%m-%d', validators=[Optional()])
    position = SelectField('Position de la bannière', choices=[
        ('top', 'Haut de page (toutes les pages)'),
        ('homepage', 'Page d\'accueil seulement'),
        ('product_page', 'Pages produits'),
        ('sidebar', 'Barre latérale')
    ], validators=[DataRequired()])
    submit = SubmitField('Enregistrer la bannière')

    def validate_on_submit(self):
        result = super().validate_on_submit()
        if not result:
            return False

        if self.start_date.data and self.end_date.data and self.start_date.data > self.end_date.data:
            self.end_date.errors.append('La date de fin ne peut pas être antérieure à la date de début.')
            return False
        return True


class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class RegistrationForm(FlaskForm):
    username = StringField("Nom d'utilisateur", 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=8), validate_password_strength])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("S'inscrire")

    def validate_username(self, username):
        user = db.session.execute(db.select(Customer).filter_by(username=username.data)).scalar_one_or_none()
        if user:
            raise ValidationError("Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")

    def validate_email(self, email):
        user = db.session.execute(db.select(Customer).filter_by(email=email.data)).scalar_one_or_none()
        if user:
            raise ValidationError('Cette adresse e-mail est déjà utilisée. Veuillez en choisir une autre.')

class ProfileForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Mettre à jour")

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.execute(db.select(Customer).filter_by(username=username.data)).scalar_one_or_none()
            if user:
                raise ValidationError("Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")

    def validate_email(self, email):
        if email.data != self.original_email:
            user = db.session.execute(db.select(Customer).filter_by(email=email.data)).scalar_one_or_none()
            if user:
                raise ValidationError('Cette adresse e-mail est déjà utilisée. Veuillez en choisir une autre.')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Ancien mot de passe', validators=[DataRequired()])
    new_password = PasswordField('Nouveau mot de passe', validators=[DataRequired(), Length(min=8), validate_password_strength])
    confirm_password = PasswordField('Confirmer le nouveau mot de passe', validators=[DataRequired(), EqualTo('new_password', message='Les mots de passe ne correspondent pas.')])
    submit = SubmitField('Changer le mot de passe')

class CategoryForm(FlaskForm):
    name = StringField('Nom de la catégorie', validators=[DataRequired(), Length(min=2, max=50)])
    submit = SubmitField('Enregistrer')

class ProductForm(FlaskForm):
    name = StringField('Nom du Produit', validators=[DataRequired(), Length(min=2, max=100)])
    category = SelectField('Catégorie', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(max=500)])
    price = FloatField('Prix (FCFA)', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    min_stock_threshold = IntegerField('Seuil de stock minimum', validators=[DataRequired(), NumberRange(min=0)], default=5)
    image_files = MultipleFileField('Images du Produit (plusieurs choix possibles)', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Seuls les fichiers images sont autorisés !')])
    submit = SubmitField('Enregistrer le Produit')

class DeleteForm(FlaskForm):
    submit = SubmitField('Supprimer')

class SendForm(FlaskForm):
    submit = SubmitField('Envoyer')

class CheckoutForm(FlaskForm):
    payment_method = RadioField('Choisissez une méthode de paiement',
                                validators=[DataRequired()])
    submit = SubmitField('Valider la commande')

    def __init__(self, *args, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        self.payment_method.choices = [
            ('cod', 'Paiement à la livraison (Espèces)'),
            ('stripe', 'Carte de crédit (Bientôt disponible)')
        ]
        if current_app.config.get('ENABLE_ORANGE_MONEY'):
            self.payment_method.choices.append(('orange_money', 'Orange Money'))
        else:
            self.payment_method.choices.append(('orange_money', 'Orange Money (Bientôt disponible)'))

        if current_app.config.get('ENABLE_WAVE_MONEY'):
            self.payment_method.choices.append(('wave_money', 'Wave Money'))
        else:
            self.payment_method.choices.append(('wave_money', 'Wave Money (Bientôt disponible)'))


class ContactForm(FlaskForm):
    name = StringField('Votre Nom', validators=[DataRequired()])
    email = StringField('Votre Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Votre Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer le message')

class StaffRegistrationForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=8), validate_password_strength])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rôle', choices=[('staff', 'Staff'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Inscrire le membre')

    def validate_username(self, username):
        user = db.session.execute(db.select(StaffUser).filter_by(username=username.data)).scalar_one_or_none()
        if user:
            raise ValidationError("Ce nom d'utilisateur est déjà pris.")

    def validate_email(self, email):
        user = db.session.execute(db.select(StaffUser).filter_by(email=email.data)).scalar_one_or_none()
        if user:
            raise ValidationError('Cette adresse e-mail est déjà utilisée.')

class StaffUserEditForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Rôle', choices=[('staff', 'Staff'), ('admin', 'Admin')], validators=[DataRequired()])
    password = PasswordField('Nouveau mot de passe (laisser vide pour ne pas changer)', validators=[Optional(), Length(min=8), validate_password_strength])
    confirm_password = PasswordField('Confirmer le nouveau mot de passe', validators=[EqualTo('password', message='Les mots de passe doivent correspondre.')])
    submit = SubmitField("Mettre à jour l'utilisateur")

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(StaffUserEditForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.execute(db.select(StaffUser).filter_by(username=username.data)).scalar_one_or_none()
            if user:
                raise ValidationError("Ce nom d'utilisateur est déjà pris.")

    def validate_email(self, email):
        if email.data != self.original_email:
            user = db.session.execute(db.select(StaffUser).filter_by(email=email.data)).scalar_one_or_none()
            if user:
                raise ValidationError('Cette adresse e-mail est déjà utilisée. Veuillez en choisir une autre.')

class ReplyForm(FlaskForm):
    subject = StringField('Objet', validators=[DataRequired()])
    message_body = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField("Envoyer l'e-mail")

class ContactMessageEditForm(FlaskForm):
    name = StringField('Nom du Client', validators=[DataRequired()])
    email = StringField('Email du Client', validators=[DataRequired(), Email()])
    message = TextAreaField('Message du Client', render_kw={'readonly': True})
    submit = SubmitField('Mettre à jour le message')

class CustomerEditForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Mettre à jour le client')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(CustomerEditForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.execute(db.select(Customer).filter_by(username=username.data)).scalar_one_or_none()
            if user:
                raise ValidationError("Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")

    def validate_email(self, email):
        if email.data != self.original_email:
            user = db.session.execute(db.select(Customer).filter_by(email=email.data)).scalar_one_or_none()
            if user:
                raise ValidationError('Cette adresse e-mail est déjà utilisée. Veuillez en choisir une autre.')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Demander la réinitialisation')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[DataRequired(), Length(min=8), validate_password_strength])
    confirm_password = PasswordField('Confirmer le nouveau mot de passe', validators=[DataRequired(), EqualTo('password', message='Les mots de passe ne correspondent pas.')])
    csrf_token = HiddenField()
    submit = SubmitField('Réinitialiser le mot de passe')

class ReviewForm(FlaskForm):
    rating = SelectField('Note', choices=[(5, '5 étoiles'), (4, '4 étoiles'), (3, '3 étoiles'), (2, '2 étoiles'), (1, '1 étoile')], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Votre avis', validators=[DataRequired()])
    submit = SubmitField('Envoyer l\'avis')

class PostForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired()])
    cover_image = FileField('Image de couverture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Images uniquement!')])
    video_url = URLField('Lien Vidéo (YouTube, etc.)', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Publier')

class PageContentForm(FlaskForm):
    title = StringField('Titre de la page', validators=[DataRequired(), Length(max=120)])
    subtitle = StringField('Sous-titre (optionnel)', validators=[Optional(), Length(max=200)])
    body = TextAreaField('Contenu principal de la page', validators=[DataRequired()])
    image_file = FileField('Image d\'en-tête', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Seules les images sont autorisées !')])
    submit = SubmitField('Enregistrer les modifications')

class NewsletterForm(FlaskForm):
    email = StringField('Votre Email', validators=[DataRequired(), Email()])
    submit = SubmitField('S\'abonner')

    def validate_email(self, email):
        subscriber = db.session.execute(db.select(NewsletterSubscriber).filter_by(email=email.data)).scalar_one_or_none()
        if subscriber:
            raise ValidationError('Cette adresse e-mail est déjà abonnée à notre newsletter.')

class NewsletterCreationForm(FlaskForm):
    subject = StringField('Sujet', validators=[DataRequired(), Length(max=150)])
    body = TextAreaField('Contenu', validators=[DataRequired()])
    submit = SubmitField('Enregistrer la newsletter')
