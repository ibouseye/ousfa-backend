from .extensions import db
from datetime import datetime, timezone
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from flask_login import UserMixin

class GetTokenMixin:
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_type': self.get_id().split('-')[0], 'user_id': self.id})

class StaffUser(db.Model, UserMixin, GetTokenMixin):
    """
    Ce modèle représente un utilisateur du personnel (administrateur, employé) du site.
    """
    __tablename__ = 'staff_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    previous_password = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='staff')

    def get_id(self):
        return f'staff-{self.id}'

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<StaffUser {self.username}>'

    posts = db.relationship('Post', back_populates='author', lazy=True)

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=1800)
            if data.get('user_type') == 'staff':
                return db.session.get(StaffUser, data.get('user_id'))
        except:
            return None

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship('Product', back_populates='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', back_populates='products')
    description = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(60), nullable=True, default='default.jpg')
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock_threshold = db.Column(db.Integer, nullable=False, default=5)
    reviews = db.relationship('Review', back_populates='product', lazy=True)
    images = db.relationship('ProductImage', back_populates='product', lazy=True, cascade="all, delete-orphan")
    order_items = db.relationship('OrderItem', back_populates='product', lazy=True)
    smart_shoppings = db.relationship('SmartShopping', back_populates='product', lazy=True)
    cart_items = db.relationship('CartItem', back_populates='product', lazy=True)

class ProductImage(db.Model):
    __tablename__ = 'product_image'
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(60), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    product = db.relationship('Product', back_populates='images')

    def __repr__(self):
        return f'<ProductImage {self.image_file} for product {self.product_id}>'

class ContactMessage(db.Model):
    __tablename__ = 'contact_message'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"ContactMessage('{self.name}', '{self.email}', '{self.date_posted}')"

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='En attente')
    status_history = db.Column(db.Text, nullable=True)
    date_ordered = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_milestone = db.Column(db.Boolean, default=False, nullable=False)

    customer = db.relationship('Customer', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Order('{self.id}', customer='{self.customer_id}', total_price='{self.total_price}')"

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    order = db.relationship('Order', back_populates='items')

    product = db.relationship('Product', back_populates='order_items')

    def __repr__(self):
        return f"OrderItem(Order ID: {self.order_id}, Product ID: {self.product_id}, Quantity: {self.quantity})"

class Customer(db.Model, UserMixin, GetTokenMixin):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    previous_password = db.Column(db.String(200), nullable=True)
    date_registered = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_id(self):
        return f'customer-{self.id}'

    orders = db.relationship('Order', back_populates='customer', lazy=True)
    cart_items = db.relationship('CartItem', back_populates='customer', lazy='dynamic', cascade="all, delete-orphan")
    wishlist_items = db.relationship('WishlistItem', back_populates='customer', lazy='dynamic', cascade="all, delete-orphan")
    reviews = db.relationship('Review', back_populates='customer', lazy=True)
    smart_shoppings = db.relationship('SmartShopping', back_populates='customer', lazy=True)
    review_votes = db.relationship('ReviewVote', back_populates='customer', lazy=True)

    def __repr__(self):
        return f'<Customer {self.username}>'

    

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=1800)
            if data.get('user_type') == 'customer':
                return db.session.get(Customer, data.get('user_id'))
        except:
            return None

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    reserved_until = db.Column(db.DateTime, nullable=True) # NOUVELLE COLONNE

    customer = db.relationship('Customer', back_populates='cart_items')
    product = db.relationship('Product', back_populates='cart_items')

    def __repr__(self):
        return f"<CartItem customer_id={self.customer_id} product_id={self.product_id} quantity={self.quantity}>"

class WishlistItem(db.Model):
    __tablename__ = 'wishlist_item'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    added_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    customer = db.relationship('Customer', back_populates='wishlist_items')
    product = db.relationship('Product')

    __table_args__ = (db.UniqueConstraint('customer_id', 'product_id', name='_customer_product_uc'),)

    def __repr__(self):
        return f"<WishlistItem customer_id={self.customer_id} product_id={self.product_id}>"

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    customer = db.relationship('Customer', back_populates='reviews')
    product = db.relationship('Product', back_populates='reviews')
    votes = db.relationship('ReviewVote', back_populates='review', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Review {self.rating}/5 for Product {self.product_id}>'

class ReviewVote(db.Model):
    __tablename__ = 'review_vote'
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vote_type = db.Column(db.String(20), nullable=False)

    review = db.relationship('Review', back_populates='votes')
    customer = db.relationship('Customer', back_populates='review_votes')

    __table_args__ = (db.UniqueConstraint('review_id', 'customer_id', name='_customer_review_uc'),)

    def __repr__(self):
        return f"<ReviewVote review_id={self.review_id} customer_id={self.customer_id} vote_type={self.vote_type}>"

class SmartShopping(db.Model):
    __tablename__ = 'smart_shopping'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    desired_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active')  # active, triggered, completed, cancelled
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    triggered_at = db.Column(db.DateTime, nullable=True)

    customer = db.relationship('Customer', back_populates='smart_shoppings')
    product = db.relationship('Product', back_populates='smart_shoppings')
    reservations = db.relationship('SmartShoppingReservation', back_populates='smart_shopping', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SmartShopping id={self.id} customer_id={self.customer_id} product_id={self.product_id} desired_price={self.desired_price}>"


class SmartShoppingReservation(db.Model):
    __tablename__ = 'smart_shopping_reservation'
    id = db.Column(db.Integer, primary_key=True)
    smart_shopping_id = db.Column(db.Integer, db.ForeignKey('smart_shopping.id'), nullable=False)
    reserved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active')  # active, completed, expired

    smart_shopping = db.relationship('SmartShopping', back_populates='reservations')

    def __repr__(self):
        return f"<SmartShoppingReservation id={self.id} smart_shopping_id={self.smart_shopping_id} status='{self.status}'>"


class Banner(db.Model):
    __tablename__ = 'banner'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(60), nullable=True, default='default_banner.jpg')
    link_url = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    position = db.Column(db.String(50), nullable=False, default='top') # 'top', 'homepage', 'sidebar', etc.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Banner '{self.title}' (Active: {self.is_active})>"

    @staticmethod
    def get_active_banners():
        from datetime import datetime
        from sqlalchemy import func, or_, select
        
        now = datetime.now(timezone.utc)
        
        return select(Banner).filter(
            Banner.is_active == True,
            or_(Banner.start_date == None, Banner.start_date <= now),
            or_(Banner.end_date == None, Banner.end_date >= now)
        )

class PageVisit(db.Model):
    __tablename__ = 'page_visit'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    session_id = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<PageVisit {self.timestamp}>'

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(60), nullable=True, default='default_post.jpg')
    video_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('staff_user.id'), nullable=False)

    author = db.relationship('StaffUser', back_populates='posts')
    images = db.relationship('PostImage', back_populates='post', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Post {self.title}>'

class PostImage(db.Model):
    __tablename__ = 'post_image'
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(60), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', back_populates='images')

    def __repr__(self):
        return f'<PostImage {self.image_file} for post {self.post_id}>'

class PageContent(db.Model):
    __tablename__ = 'page_content'
    page_name = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(120), nullable=True)
    subtitle = db.Column(db.String(200), nullable=True)
    body = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(60), nullable=True)

    def __repr__(self):
        return f'<PageContent {self.page_name}>'

class Milestone(db.Model):
    __tablename__ = 'milestone'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.Integer, unique=True, nullable=False)

    def __repr__(self):
        return f'<Milestone {self.order_number}>'

class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscriber'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<NewsletterSubscriber {self.email}>"

class Newsletter(db.Model):
    __tablename__ = 'newsletter'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    sent = db.Column(db.Boolean, default=False)
    archived = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Newsletter {self.subject}>'