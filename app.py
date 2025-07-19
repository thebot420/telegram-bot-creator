from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import uuid
import datetime
import telegram
import logging
import asyncio # NEW: Import the asyncio library

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- App & DB Initialization ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bots.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Telegram Bot Setup ---
telegram_bots = {}
SERVER_URL = "https://telegram-bot-creator.onrender.com"

# --- Database Models ---
# (These classes remain the same)
class Bot(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = db.Column(db.String(100), unique=True, nullable=False)
    wallet = db.Column(db.String(100), nullable=False)
    products = db.relationship('Product', backref='bot', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='bot', lazy=True, cascade="all, delete-orphan")
    def to_dict(self):
        return {'id': self.id, 'token': self.token, 'wallet': self.wallet, 'products': [p.to_dict() for p in self.products], 'orders': [o.to_dict() for o in self.orders]}

class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    bot_id = db.Column(db.String(36), db.ForeignKey('bot.id'), nullable=False)
    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'price': self.price}

class Order(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bot_id = db.Column(db.String(36), db.ForeignKey('bot.id'), nullable=False)
    def to_dict(self):
        return {'id': self.id, 'product_name': self.product_name, 'price': self.price, 'timestamp': self.timestamp.isoformat()}

# --- Telegram Bot Functions (Now Async) ---
async def setup_bot(bot_token):
    """Initializes a bot and sets its webhook asynchronously."""
    logging.info("--- 1. ENTERED async setup_bot function ---")
    if not bot_token:
        logging.error("--- ERROR: bot_token is empty or None ---")
        return

    if bot_token not in telegram_bots:
        logging.info(f"--- 2. Initializing bot with token: {bot_token[:10]}... ---")
        bot = telegram.Bot(token=bot_token)
        webhook_url = f"{SERVER_URL}/webhook/{bot_token}"
        logging.info(f"--- 3. Webhook URL to be set: {webhook_url} ---")
        try:
            # NEW: Use 'await' for the async function
            await bot.set_webhook(webhook_url)
            telegram_bots[bot_token] = bot
            logging.info(f"--- 4. SUCCESS: Webhook set successfully ---")
        except Exception as e:
            logging.error(f"--- 4. ERROR: Failed to set webhook. Reason: {e} ---")

async def handle_telegram_update(bot_token, update_data):
    """Handles an incoming message from Telegram asynchronously."""
    if bot_token not in telegram_bots:
        await setup_bot(bot_token)
        if bot_token not in telegram_bots: return

    update = telegram.Update.de_json(update_data, telegram_bots[bot_token])
    if not update.message or not update.message.text: return

    chat_id = update.message.chat_id
    message_text = update.message.text
    
    bot_data = Bot.query.filter_by(token=bot_token).first()
    if not bot_data: return

    if message_text.startswith('/buy'):
        try:
            product_name = message_text.split(' ', 1)[1]
            product_to_buy = next((p for p in bot_data.products if p.name.lower() == product_name.lower()), None)
            if product_to_buy:
                new_order = Order(product_name=product_to_buy.name, price=product_to_buy.price, bot_id=bot_data.id)
                db.session.add(new_order)
                db.session.commit()
                reply_text = f"Thank you for your order! To purchase '{product_to_buy.name}', please send {product_to_buy.price} to this wallet:\n\n`{bot_data.wallet}`"
            else:
                reply_text = f"Sorry, the product '{product_name}' was not found."
        except IndexError:
            reply_text = "To buy a product, please use the format: /buy <Product Name>"
    else:
        if not bot_data.products:
            reply_text = "This shop has no products yet."
        else:
            product_list = [f"- {p.name} ({p.price})" for p in bot_data.products]
            reply_text = "Welcome! Here are our products:\n\n" + "\n".join(product_list) + "\n\nTo buy, type: /buy <Product Name>"
    
    # NEW: Use 'await' for the async function
    await telegram_bots[bot_token].send_message(chat_id=chat_id, text=reply_text, parse_mode='Markdown')

# --- API ROUTES ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('email') == 'user@example.com' and data.get('password') == 'password123':
        return jsonify({'message': 'Login successful!'}), 200
    return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/api/bots', methods=['POST'])
def create_bot():
    logging.info("\n--- A. ENTERED create_bot endpoint ---")
    data = request.get_json()
    bot_token = data.get('bot_token')
    logging.info(f"--- B. Received token from frontend: {bot_token[:10]}... ---")
    
    if Bot.query.filter_by(token=bot_token).first():
        logging.warning("--- C. Bot with this token already exists. Aborting. ---")
        return jsonify({'message': 'A bot with this token already exists.'}), 409

    new_bot = Bot(token=bot_token, wallet=data.get('wallet_address'))
    db.session.add(new_bot)
    db.session.commit()
    logging.info("--- D. Bot saved to database successfully. ---")
    
    logging.info("--- E. Calling setup_bot function... ---")
    # NEW: Use asyncio.run() to call the async function from our sync code
    asyncio.run(setup_bot(bot_token))
    logging.info("--- F. Returned from setup_bot function. ---")
    
    return jsonify(new_bot.to_dict()), 201

@app.route('/webhook/<bot_token>', methods=['POST'])
def telegram_webhook(bot_token):
    # NEW: Use asyncio.run() to call the async function from our sync code
    asyncio.run(handle_telegram_update(bot_token, request.get_json()))
    return "ok", 200

# (All other routes remain the same)
@app.route('/api/bots', methods=['GET'])
def get_bots():
    bots = Bot.query.all()
    return jsonify([b.to_dict() for b in bots])

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

@app.route('/api/bots/<bot_id>/products', methods=['POST'])
def add_product_to_bot(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot: return jsonify({'message': 'Bot not found'}), 404
    data = request.get_json()
    new_product = Product(name=data.get('name'), price=float(data.get('price')), bot_id=bot.id)
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

@app.route('/<path:path>')
def serve_static_files(path): return send_from_directory('.', path)
