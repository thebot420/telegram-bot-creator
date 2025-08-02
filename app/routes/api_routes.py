from flask import Blueprint, request, jsonify, current_app
from .. import db
from ..models import User, Bot, Category, Product, Order
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
import asyncio
import os
import requests
import hmac
import hashlib
import json

# This Blueprint will handle all our API logic.
api = Blueprint('api', __name__)

# --- NOWPayments & Telegram Bot Setup ---
SERVER_URL = "https://telegram-bot-creator.onrender.com"
NOWPAYMENTS_API_KEY = os.environ.get('NOWPAYMENTS_API_KEY')
NOWPAYMENTS_IPN_SECRET_KEY = os.environ.get('NOWPAYMENTS_IPN_SECRET_KEY')

# --- Helper function to run async code ---
def run_async(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

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
    with current_app.app_context():
        order_to_update = db.session.get(Order, order.id)
        if not order_to_update: return

        seller_wallet = order_to_update.bot.owner.wallet
        payout_amount = order_to_update.price * 0.99
        payout_currency = "usdttrc20"
        headers = {'x-api-key': NOWPAYMENTS_API_KEY}
        payload = {"withdrawals": [{"address": seller_wallet, "currency": payout_currency, "amount": payout_amount}]}
        response = requests.post('https://api.nowpayments.io/v1/payout', headers=headers, json=payload)
        
        if response.ok:
            logging.info(f"--- SUCCESS: Payout for order {order.id} created successfully. ---")
            order_to_update.payout_status = 'paid'
        else:
            logging.error(f"--- ERROR: NOWPayments payout failed for order {order.id}. Response: {response.text} ---")
            order_to_update.payout_status = 'failed'
        db.session.commit()

async def handle_telegram_update(bot_token, update_data):
    logging.info(f"--- Handling update for bot token: {bot_token[:10]}... ---")
    bot = telegram.Bot(token=bot_token)
    update = telegram.Update.de_json(update_data, bot)
    
    with current_app.app_context():
        bot_data = Bot.query.filter_by(token=bot_token).first()
        if not bot_data or not bot_data.owner.is_active: 
            logging.warning(f"--- Bot owner inactive or bot not found for token {bot_token[:10]}... ---")
            return
        
        if update.callback_query:
            query = update.callback_query
            chat_id = query.message.chat_id
            data = query.data
            await query.answer()
            
            if data == 'main_menu':
                keyboard = [
                    [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
                    [InlineKeyboardButton("⭐️ Reviews", callback_data="reviews")],
                    [InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
                    [InlineKeyboardButton("🎫 Support Tickets", callback_data="support")],
                    [InlineKeyboardButton("📞 Contact Us", callback_data="contact")],
                    [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text=bot_data.welcome_message, reply_markup=reply_markup)
                return

            parts = data.split(':')
            action = parts[0]
            item_id = parts[1] if len(parts) > 1 else None

            if action == 'browse_products':
                main_categories = [c for c in bot_data.categories if c.parent_id is None]
                if not main_categories:
                    await query.edit_message_text(text="This shop has no categories yet.")
                    return
                keyboard = [[InlineKeyboardButton(c.name, callback_data=f"view_category:{c.id}")] for c in main_categories]
                keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text="Please select a category:", reply_markup=reply_markup)

            elif action == 'view_category':
                category = db.session.get(Category, item_id)
                if not category: return
                
                if category.sub_categories:
                    keyboard = [[InlineKeyboardButton(sc.name, callback_data=f"view_category:{sc.id}")] for sc in category.sub_categories]
                    back_button_data = f"view_category:{category.parent_id}" if category.parent_id else "browse_products"
                    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=back_button_data)])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(text=f"Sub-categories in {category.name}:", reply_markup=reply_markup)
                elif category.products:
                    await query.edit_message_text(text=f"Products in {category.name}:")
                    for product in category.products:
                        caption = f"**{product.name}**\nPrice: {product.price} / {product.unit}"
                        keyboard = [[InlineKeyboardButton(f"Buy {product.name}", callback_data=f"buy_product:{product.id}")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        if product.image_url:
                            await bot.send_photo(chat_id=chat_id, photo=product.image_url, caption=caption, reply_markup=reply_markup, parse_mode='Markdown')
                        else:
                            await bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup, parse_mode='Markdown')
                    back_button_data = f"view_category:{category.parent_id}" if category.parent_id else "browse_products"
                    await bot.send_message(chat_id=chat_id, text="Go back?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_button_data)]]))
                else:
                    await query.edit_message_text(text=f"No products or sub-categories found in {category.name}.")

            # --- THIS IS THE CRITICAL FIX ---
            elif action == 'buy_product':
                product = db.session.get(Product, item_id)
                if product:
                    # Step 1: Create the order in our database
                    new_order = Order(product_name=product.name, price=product.price, bot_id=product.category.bot_id)
                    db.session.add(new_order)
                    db.session.commit()
                    
                    # Step 2: Talk directly to NOWPayments
                    if not NOWPAYMENTS_API_KEY:
                        logging.error("NOWPayments API key is not set.")
                        await bot.send_message(chat_id=chat_id, text="Sorry, the payment system is not configured.")
                        return

                    headers = {'x-api-key': NOWPAYMENTS_API_KEY}
                    payload = {"price_amount": product.price, "price_currency": "usd", "order_id": new_order.id, "ipn_callback_url": f"{SERVER_URL}/webhook/nowpayments"}
                    
                    try:
                        response = requests.post('https://api.nowpayments.io/v1/invoice', headers=headers, json=payload)
                        if response.ok:
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
            keyboard = [
                [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
                [InlineKeyboardButton("⭐️ Reviews", callback_data="reviews")],
                [InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
                [InlineKeyboardButton("🎫 Support Tickets", callback_data="support")],
                [InlineKeyboardButton("📞 Contact Us", callback_data="contact")],
                [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot.send_message(chat_id=chat_id, text=bot_data.welcome_message, reply_markup=reply_markup)

# --- API ROUTES ---
@api.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.is_active and user.check_password(data.get('password')):
        return jsonify({'message': 'Login successful!', 'userId': user.id}), 200
    return jsonify({'message': 'Invalid email or password'}), 401

@api.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASSWORD = "supersecretpassword123"
    if data.get('email') == ADMIN_EMAIL and data.get('password') == ADMIN_PASSWORD:
        return jsonify({'message': 'Admin login successful!'}), 200
    return jsonify({'message': 'Invalid admin credentials'}), 401

@api.route('/api/admin/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@api.route('/api/admin/users', methods=['POST'])
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

@api.route('/api/admin/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

@api.route('/api/admin/users/<user_id>', methods=['GET'])
def get_user_details(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    return jsonify(user.to_dict())

@api.route('/api/admin/users/<user_id>/toggle-active', methods=['POST'])
def toggle_user_active(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'message': f'User status changed to {user.is_active}'}), 200

@api.route('/api/admin/users/<user_id>/update-email', methods=['POST'])
def update_user_email(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    new_email = data.get('email')
    if not new_email: return jsonify({'message': 'New email is required.'}), 400
    user.email = new_email
    db.session.commit()
    return jsonify({'message': 'User email updated successfully'}), 200

@api.route('/api/admin/users/<user_id>/reset-password', methods=['POST'])
def reset_user_password(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    new_password = data.get('password')
    if not new_password: return jsonify({'message': 'New password is required.'}), 400
    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'User password reset successfully'}), 200

@api.route('/api/admin/orders', methods=['GET'])
def get_all_orders():
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    orders_with_user_info = []
    for order in orders:
        order_data = order.to_dict()
        order_data['user_email'] = order.bot.owner.email
        orders_with_user_info.append(order_data)
    return jsonify(orders_with_user_info)

@api.route('/api/admin/dashboard-stats', methods=['GET'])
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

@api.route('/api/users/<user_id>/dashboard-stats', methods=['GET'])
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

@api.route('/webhook/nowpayments', methods=['POST'])
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

@api.route('/api/bots', methods=['POST'])
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

@api.route('/webhook/<bot_token>', methods=['POST'])
def telegram_webhook(bot_token):
    run_async(handle_telegram_update(bot_token, request.get_json()))
    return "ok", 200

@api.route('/api/users/<user_id>/bots', methods=['GET'])
def get_user_bots(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    return jsonify([bot.to_dict() for bot in user.bots])

@api.route('/api/bots/<bot_id>', methods=['DELETE'])
def delete_bot(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot: return jsonify({'message': 'Bot not found'}), 404
    db.session.delete(bot)
    db.session.commit()
    return jsonify({'message': 'Bot deleted successfully'}), 200

@api.route('/api/bots/<bot_id>', methods=['GET'])
def get_bot_details(bot_id):
    bot = db.session.get(Bot, bot_id)
    if bot: return jsonify(bot.to_dict())
    return jsonify({'message': 'Bot not found'}), 404

@api.route('/api/bots/<bot_id>/welcome-message', methods=['POST'])
def update_welcome_message(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot: return jsonify({'message': 'Bot not found'}), 404
    data = request.get_json()
    bot.welcome_message = data.get('message', '')
    db.session.commit()
    return jsonify({'message': 'Welcome message updated successfully.'}), 200

@api.route('/api/bots/<bot_id>/categories', methods=['POST'])
def create_category(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot: return jsonify({'message': 'Bot not found'}), 404
    data = request.get_json()
    parent_id = data.get('parent_id')
    new_category = Category(name=data.get('name'), bot_id=bot.id, parent_id=parent_id)
    db.session.add(new_category)
    db.session.commit()
    return jsonify(new_category.to_dict()), 201

@api.route('/api/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if not category: return jsonify({'message': 'Category not found'}), 404
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted successfully'}), 200

@api.route('/api/bots/<bot_id>/products', methods=['POST'])
def add_product_to_bot(bot_id):
    data = request.get_json()
    category_id = data.get('category_id')
    category = db.session.get(Category, category_id)
    if not category or category.bot_id != bot_id: return jsonify({'message': 'Category not found or does not belong to this bot'}), 404
    new_product = Product(name=data.get('name'), price=float(data.get('price')), unit=data.get('unit'), image_url=data.get('image_url'), video_url=data.get('video_url'), category_id=category.id)
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201
    
@api.route('/api/bots/<bot_id>/orders', methods=['GET'])
def get_bot_orders(bot_id):
    bot = db.session.get(Bot, bot_id)
    if bot: return jsonify([o.to_dict() for o in bot.orders])
    return jsonify({'message': 'Bot not found'}), 404

# Add this entire function to the bottom of your app/routes/api_routes.py file

@api.route('/debug-paths')
def debug_paths():
    """A special route to debug file paths on the live server."""
    # Get the application context to inspect its properties
    app = current_app._get_current_object()
    
    # Build a dictionary of important paths
    paths = {
        "app.root_path": app.root_path,
        "app.template_folder": app.template_folder,
        "expected_template_path": os.path.join(app.root_path, app.template_folder),
        "index.html_exists": os.path.exists(os.path.join(app.root_path, app.template_folder, 'index.html'))
    }
    
    return jsonify(paths)
