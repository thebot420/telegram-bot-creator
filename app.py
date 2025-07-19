from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import uuid
import datetime

# --- App & DB Initialization ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bots.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class Bot(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = db.Column(db.String(100), nullable=False)
    wallet = db.Column(db.String(100), nullable=False)
    products = db.relationship('Product', backref='bot', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='bot', lazy=True, cascade="all, delete-orphan")
    def to_dict(self): return {'id': self.id, 'token': self.token, 'wallet': self.wallet, 'products': [p.to_dict() for p in self.products], 'orders': [o.to_dict() for o in self.orders]}

class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    bot_id = db.Column(db.String(36), db.ForeignKey('bot.id'), nullable=False)
    def to_dict(self): return {'id': self.id, 'name': self.name, 'price': self.price}

class Order(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    bot_id = db.Column(db.String(36), db.ForeignKey('bot.id'), nullable=False)
    def to_dict(self): return {'id': self.id, 'product_name': self.product_name, 'price': self.price, 'timestamp': self.timestamp.isoformat()}

# --- API ROUTES ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('email') == 'user@example.com' and data.get('password') == 'password123':
        return jsonify({'message': 'Login successful!'}), 200
    return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/api/bots', methods=['GET'])
def get_bots():
    bots = Bot.query.all()
    return jsonify([b.to_dict() for b in bots])

@app.route('/api/bots', methods=['POST'])
def create_bot():
    data = request.get_json()
    new_bot = Bot(token=data.get('bot_token'), wallet=data.get('wallet_address'))
    db.session.add(new_bot)
    db.session.commit()
    return jsonify(new_bot.to_dict()), 201

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

# --- This block is needed to run the server locally ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)