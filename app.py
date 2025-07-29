from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
import asyncio
import os
import requests
import hmac
import hashlib
import json

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- App & DB Initialization ---
app = Flask(__name__)
# --- YOUR DATABASE URL HAS BEEN INCLUDED ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bot_database_4xww_user:ZvtsS6mD0QRjPVKEH2w83fcBpeMonpnM@dpg-d1uifimmcj7s73eifvcg-a/bot_database_4xww'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- NOWPayments & Telegram Bot Setup ---
SERVER_URL = "https://telegram-bot-creator.onrender.com"
NOWPAYMENTS_API_KEY = os.environ.get('NOWPAYMENTS_API_KEY')
NOWPAYMENTS_IPN_SECRET_KEY = os.environ.get('NOWPAYMENTS_IPN_SECRET_KEY')

# --- Helper function to run async code robustly ---
def run_async(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

# --- Database Models ---
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
    categories = db.relationship('Category', backref='bot', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='bot', lazy=True, cascade="all, delete-orphan")
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    def to_dict(self): return {'id': self.id, 'token': self.token, 'wallet': self.wallet, 'categories': [c.to_dict() for c in self.categories], 'orders': [o.to_dict() for o in self.orders]}
    def to_dict_simple(self): return {'id': self.id, 'token_snippet': f"{self.token[:6]}..."}

class Category(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    bot_id = db.Column(db.String(36), db.ForeignKey('bot.id'), nullable=False)
    products = db.relationship('Product', backref='category', lazy=True, cascade="all, delete-orphan")
    def to_dict(self): return {'id': self.id, 'name': self.name, 'products': [p.to_dict() for p in self.products]}

class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    category_id = db.Column(db.String(36), db.ForeignKey('category.id'), nullable=False)
    def to_dict(self): return {'id': self.id, 'name': self.name, 'price': self.price, 'image_url': self.image_url, 'video_url': self.video_url}

class Order(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='pending', nullable=False)
    payout_status = db.Column(db.String(20), default='unpaid', nullable=False)
    bot_id = db.Column(db.String(36), db.ForeignKey('bot.id'), nullable=False)
    def to_dict(self): return {'id': self.id, 'product_name': self.product_name, 'price': self.price, 'timestamp': self.timestamp.isoformat(), 'status': self.status}

# --- Telegram & Payment Functions ---
async def setup_bot_webhook(bot_token):
    logging.info(f"Setting up webhook for token: {bot_token[:10]}... ---")
    bot = telegram.Bot(token=bot_token)
    webhook_url = f"{SERVER_URL}/webhook/{bot_token}"
    try:
        await bot.set_webhook(webhook_url)
        logging.info(f"--- SUCCESS: Webhook set successfully for {bot_token[:10]}... ---")
    except Exception as e:
        logging.error(f"--- ERROR: Failed to set webhook for {bot_token[:10]}. Reason: {e} ---")

def execute_payout(order):
    logging.info(f"--- Initiating payout for order {order.id} ---")
    seller_wallet = order.bot.owner.wallet
    payout_amount = order.price * 0.99
    payout_currency = "usdttrc20"
    headers = {'x-api-key': NOWPAYMENTS_API_KEY}
    payload = {"withdrawals": [{"address": seller_wallet, "currency": payout_currency, "amount": payout_amount}]}
    response = requests.post('https://api.nowpayments.io/v1/payout', headers=headers, json=payload)
    if response.status_code == 201:
        logging.info(f"--- SUCCESS: Payout for order {order.id} created successfully. ---")
        order.payout_status = 'paid'
        db.session.commit()
    else:
        logging.error(f"--- ERROR: NOWPayments payout failed for order {order.id}. Response: {response.text} ---")
        order.payout_status = 'failed'
        db.session.commit()

async def handle_telegram_update(bot_token, update_data):
    logging.info(f"--- Handling update for bot token: {bot_token[:10]}... ---")
    bot = telegram.Bot(token=bot_token)
    update = telegram.Update.de_json(update_data, bot)
    with app.app_context():
        bot_data = Bot.query.filter_by(token=bot_token).first()
        if not bot_data or not bot_data.owner.is_active: 
            logging.warning(f"--- Bot owner inactive or bot not found for token {bot_token[:10]}... ---")
            return
        if update.callback_query:
            query = update.callback_query
            chat_id = query.message.chat_id
            data = query.data
            await query.answer()
            action, item_id = data.split(':')
            if action == 'view_category':
                category = db.session.get(Category, item_id)
                if not category or not category.products:
                    await bot.send_message(chat_id=chat_id, text=f"No products found in {category.name}.")
                    return
                for product in category.products:
                    caption = f"{product.name}\nPrice: {product.price}"
                    keyboard = [[InlineKeyboardButton(f"Buy {product.name}", callback_data=f"buy_product:{product.id}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    if product.image_url:
                        await bot.send_photo(chat_id=chat_id, photo=product.image_url, caption=caption, reply_markup=reply_markup)
                    else:
                        await bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup)
            elif action == 'buy_product':
                product = db.session.get(Product, item_id)
                if product:
                    new_order = Order(product_name=product.name, price=product.price, bot_id=product.category.bot_id)
                    db.session.add(new_order)
                    db.session.commit()
                    if not NOWPAYMENTS_API_KEY:
                        logging.error("NOWPayments API key is not set.")
                        await bot.send_message(chat_id=chat_id, text="Sorry, the payment system is not configured.")
                        return
                    headers = {'x-api-key': NOWPAYMENTS_API_KEY}
                    payload = {"price_amount": product.price, "price_currency": "usd", "order_id": new_order.id, "ipn_callback_url": f"{SERVER_URL}/webhook/nowpayments"}
                    try:
                        response = requests.post('https://api.nowpayments.io/v1/invoice', headers=headers, json=payload)
                        if response.status_code == 201:
                            payment_info = response.json()
                            invoice_url = payment_info.get('invoice_url')
                            reply_text = f"To complete your purchase of '{product.name}', please use the following secure payment link:\n\n{invoice_url}"
                            await bot.send_message(chat_id=chat_id, text=reply_text)
                        else:
                            logging.error(f"NOWPayments error creating invoice: {response.text}")
                            await bot.send_message(chat_id=chat_id, text="Sorry, there was an error creating your payment.")
                    except Exception as e:
                        logging.error(f"Exception calling NOWPayments: {e}")
                        await bot.send_message(chat_id=chat_id, text="A critical error occurred.")
        elif update.message and update.message.text:
            chat_id = update.message.chat_id
            if not bot_data.categories:
                await bot.send_message(chat_id=chat_id, text="This shop is not set up yet.")
                return
            keyboard = [[InlineKeyboardButton(c.name, callback_data=f"view_category:{c.id}")] for c in bot_data.categories]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot.send_message(chat_id=chat_id, text="Welcome! Please select a category:", reply_markup=reply_markup)

# --- API ROUTES ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.is_active and user.check_password(data.get('password')):
        return jsonify({'message': 'Login successful!', 'userId': user.id}), 200
    return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASSWORD = "supersecretpassword123"
    if data.get('email') == ADMIN_EMAIL and data.get('password') == ADMIN_PASSWORD:
        return jsonify({'message': 'Admin login successful!'}), 200
    return jsonify({'message': 'Invalid admin credentials'}), 401

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/admin/users', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password: return jsonify({'message': 'Email and password are required.'}), 400
    if User.query.filter_by(email=email).first(): return jsonify({'message': 'User with this email already exists.'}), 409
    new_user = User(email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

@app.route('/api/admin/users/<user_id>', methods=['GET'])
def get_user_details(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    return jsonify(user.to_dict())

@app.route('/api/admin/users/<user_id>/toggle-active', methods=['POST'])
def toggle_user_active(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'message': f'User status changed to {user.is_active}'}), 200

@app.route('/api/admin/users/<user_id>/update-email', methods=['POST'])
def update_user_email(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    new_email = data.get('email')
    if not new_email: return jsonify({'message': 'New email is required.'}), 400
    user.email = new_email
    db.session.commit()
    return jsonify({'message': 'User email updated successfully'}), 200

@app.route('/api/admin/users/<user_id>/reset-password', methods=['POST'])
def reset_user_password(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    new_password = data.get('password')
    if not new_password: return jsonify({'message': 'New password is required.'}), 400
    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'User password reset successfully'}), 200

@app.route('/api/admin/orders', methods=['GET'])
def get_all_orders():
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    orders_with_user_info = []
    for order in orders:
        order_data = order.to_dict()
        order_data['user_email'] = order.bot.owner.email
        orders_with_user_info.append(order_data)
    return jsonify(orders_with_user_info)

@app.route('/api/admin/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    total_sales = db.session.query(db.func.sum(Order.price)).scalar() or 0
    total_orders = Order.query.count()
    commission_earned = total_sales * 0.01
    active_users = User.query.filter_by(is_active=True).count()
    recent_orders_query = Order.query.order_by(Order.timestamp.desc()).limit(5).all()
    recent_orders = []
    for order in recent_orders_query:
        order_data = order.to_dict()
        order_data['user_email'] = order.bot.owner.email
        recent_orders.append(order_data)
    stats = {'total_sales': round(total_sales, 2), 'commission_earned': round(commission_earned, 2), 'total_orders': total_orders, 'active_users': active_users, 'recent_orders': recent_orders}
    return jsonify(stats)

@app.route('/api/users/<user_id>/dashboard-stats', methods=['GET'])
def get_user_dashboard_stats(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    bot_ids = [bot.id for bot in user.bots]
    total_sales = db.session.query(db.func.sum(Order.price)).filter(Order.bot_id.in_(bot_ids)).scalar() or 0
    total_orders = Order.query.filter(Order.bot_id.in_(bot_ids)).count()
    recent_orders_query = Order.query.filter(Order.bot_id.in_(bot_ids)).order_by(Order.timestamp.desc()).limit(5).all()
    recent_orders = [order.to_dict() for order in recent_orders_query]
    stats = {'total_sales': round(total_sales, 2), 'total_orders': total_orders, 'recent_orders': recent_orders}
    return jsonify(stats)

@app.route('/api/orders/<product_id>/create-payment', methods=['POST'])
def create_payment(product_id):
    product = db.session.get(Product, product_id)
    if not product: return jsonify({'message': 'Product not found'}), 404
    new_order = Order(product_name=product.name, price=product.price, bot_id=product.category.bot_id)
    db.session.add(new_order)
    db.session.commit()
    if not NOWPAYMENTS_API_KEY:
        logging.error("NOWPayments API key is not set.")
        return jsonify({'message': 'Payment processor is not configured.'}), 500
    headers = {'x-api-key': NOWPAYMENTS_API_KEY}
    payload = {"price_amount": product.price, "price_currency": "usd", "order_id": new_order.id, "ipn_callback_url": f"{SERVER_URL}/webhook/nowpayments"}
    response = requests.post('https://api.nowpayments.io/v1/invoice', headers=headers, json=payload)
    if response.status_code == 201:
        payment_data = response.json()
        return jsonify({'invoice_url': payment_data.get('invoice_url')}), 201
    else:
        logging.error(f"NOWPayments error: {response.text}")
        return jsonify({'message': 'Failed to create payment invoice.'}), 500

@app.route('/webhook/nowpayments', methods=['POST'])
def nowpayments_webhook():
    signature = request.headers.get('x-nowpayments-sig')
    if not signature or not NOWPAYMENTS_IPN_SECRET_KEY: return "Configuration error", 400
    try:
        sorted_payload = json.dumps(request.get_json(), sort_keys=True, separators=(',', ':')).encode('utf-8')
        expected_signature = hmac.new(NOWPAYMENTS_IPN_SECRET_KEY.encode('utf-8'), sorted_payload, hashlib.sha512).hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            logging.warning("Invalid IPN signature from NOWPayments.")
            return "Invalid signature", 400
    except Exception as e:
        logging.error(f"Error during signature verification: {e}")
        return "Verification error", 400
    data = request.get_json()
    order_id = data.get('order_id')
    payment_status = data.get('payment_status')
    order = db.session.get(Order, order_id)
    if order and payment_status == 'finished' and order.payout_status == 'unpaid':
        order.status = 'paid'
        db.session.commit()
        logging.info(f"Order {order_id} marked as paid.")
        execute_payout(order)
    return "ok", 200

@app.route('/api/bots', methods=['POST'])
def create_bot():
    data = request.get_json()
    bot_token = data.get('bot_token')
    user_id = data.get('userId')
    if not user_id: return jsonify({'message': 'User ID is missing.'}), 400
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found.'}), 404
    if Bot.query.filter_by(token=bot_token).first(): return jsonify({'message': 'A bot with this token already exists.'}), 409
    new_bot = Bot(token=bot_token, wallet=data.get('wallet_address'), user_id=user.id)
    db.session.add(new_bot)
    db.session.commit()
    run_async(setup_bot_webhook(bot_token))
    return jsonify(new_bot.to_dict()), 201

@app.route('/webhook/<bot_token>', methods=['POST'])
def telegram_webhook(bot_token):
    run_async(handle_telegram_update(bot_token, request.get_json()))
    return "ok", 200

@app.route('/api/users/<user_id>/bots', methods=['GET'])
def get_user_bots(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    return jsonify([bot.to_dict() for bot in user.bots])

@app.route('/api/bots/<bot_id>', methods=['DELETE'])
def delete_bot(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot: return jsonify({'message': 'Bot not found'}), 404
    db.session.delete(bot)
    db.session.commit()
    return jsonify({'message': 'Bot deleted successfully'}), 200

@app.route('/api/bots/<bot_id>', methods=['GET'])
def get_bot_details(bot_id):
    bot = db.session.get(Bot, bot_id)
    if bot: return jsonify(bot.to_dict())
    return jsonify({'message': 'Bot not found'}), 404

@app.route('/api/bots/<bot_id>/categories', methods=['POST'])
def create_category(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot: return jsonify({'message': 'Bot not found'}), 404
    data = request.get_json()
    new_category = Category(name=data.get('name'), bot_id=bot.id)
    db.session.add(new_category)
    db.session.commit()
    return jsonify(new_category.to_dict()), 201

@app.route('/api/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if not category: return jsonify({'message': 'Category not found'}), 404
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted successfully'}), 200

@app.route('/api/bots/<bot_id>/products', methods=['POST'])
def add_product_to_bot(bot_id):
    data = request.get_json()
    category_id = data.get('category_id')
    category = db.session.get(Category, category_id)
    if not category or category.bot_id != bot_id: return jsonify({'message': 'Category not found or does not belong to this bot'}), 404
    new_product = Product(name=data.get('name'), price=float(data.get('price')), image_url=data.get('image_url'), video_url=data.get('video_url'), category_id=category.id)
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201
    
@app.route('/api/bots/<bot_id>/orders', methods=['GET'])
def get_bot_orders(bot_id):
    bot = db.session.get(Bot, bot_id)
    if bot: return jsonify([o.to_dict() for o in bot.orders])
    return jsonify({'message': 'Bot not found'}), 404

# --- PAGE SERVING ROUTES ---
@app.route('/')
def serve_login_page(): return send_from_directory('.', 'index.html')
@app.route('/dashboard.html')
def serve_dashboard(): return send_from_directory('.', 'dashboard.html')
@app.route('/manage/<bot_id>')
def serve_manage_page(bot_id): return send_from_directory('.', 'manage.html')
@app.route('/orders/<bot_id>')
def serve_orders_page(bot_id): return send_from_directory('.', 'orders.html')
@app.route('/admin')
def serve_admin_login_page(): return send_from_directory('.', 'admin.html')
@app.route('/admin/dashboard')
def serve_admin_dashboard(): return send_from_directory('.', 'admin_main_dashboard.html')
@app.route('/admin/users')
def serve_admin_users_page(): return send_from_directory('.', 'admin_users.html')
@app.route('/admin/users/<user_id>')
def serve_user_details_page(user_id): return send_from_directory('.', 'admin_user_details.html')
@app.route('/admin/orders')
def serve_master_orders_page(): return send_from_directory('.', 'admin_orders.html')
@app.route('/<path:path>')
def serve_static_files(path): return send_from_directory('.', path)