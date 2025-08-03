from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    bots = db.relationship('Bot', backref='owner', lazy=True, cascade="all, delete-orphan")
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    def to_dict(self): return {'id': self.id, 'email': self.email, 'is_active': self.is_active, 'bots': [bot.to_dict_simple() for bot in self.bots]}

class Bot(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = db.Column(db.String(100), unique=True, nullable=False)
    wallet = db.Column(db.String(100), nullable=False)
    welcome_message = db.Column(db.String(1024), default="Welcome to my shop!")
    categories = db.relationship('Category', backref='bot', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='bot', lazy=True, cascade="all, delete-orphan")
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    def to_dict(self): 
        return {
            'id': self.id, 'token': self.token, 'wallet': self.wallet, 
            'welcome_message': self.welcome_message,
            'categories': [c.to_dict() for c in self.categories if c.parent_id is None], 
            'orders': [o.to_dict() for o in self.orders]
        }
    def to_dict_simple(self): return {'id': self.id, 'token_snippet': f"{self.token[:6]}..."}

class Category(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    bot_id = db.Column(db.String(36), db.ForeignKey('bot.id'), nullable=False)
    parent_id = db.Column(db.String(36), db.ForeignKey('category.id'), nullable=True)
    sub_categories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), cascade="all, delete-orphan")
    products = db.relationship('Product', backref='category', lazy=True, cascade="all, delete-orphan")
    def to_dict(self): 
        return {
            'id': self.id, 'name': self.name, 'parent_id': self.parent_id,
            'sub_categories': [sc.to_dict() for sc in self.sub_categories],
            'products': [p.to_dict() for p in self.products]
        }

class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1024), nullable=True)
    unit = db.Column(db.String(20), default='item')
    # --- THIS IS THE CRITICAL FIX ---
    image_url = db.Column(db.Text, nullable=True) # Changed from String(500) to Text
    video_url = db.Column(db.Text, nullable=True) # Changed from String(500) to Text
    category_id = db.Column(db.String(36), db.ForeignKey('category.id'), nullable=False)
    price_tiers = db.relationship('PriceTier', backref='product', lazy=True, cascade="all, delete-orphan")
    def to_dict(self): 
        return {
            'id': self.id, 'name': self.name, 'description': self.description, 
            'unit': self.unit, 'image_url': self.image_url, 'video_url': self.video_url,
            'price_tiers': [pt.to_dict() for pt in self.price_tiers]
        }

class PriceTier(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    label = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'), nullable=False)
    def to_dict(self):
        return {'id': self.id, 'label': self.label, 'price': self.price}

class Order(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='pending', nullable=False)
    payout_status = db.Column(db.String(20), default='unpaid', nullable=False)
    bot_id = db.Column(db.String(36), db.ForeignKey('bot.id'), nullable=False)
    def to_dict(self): return {'id': self.id, 'product_name': self.product_name, 'price': self.price, 'timestamp': self.timestamp.isoformat(), 'status': self.status}
