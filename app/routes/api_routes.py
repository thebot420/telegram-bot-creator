import os
import logging
import asyncio
import requests
import hmac
import hashlib
import json
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import cloudinary
import cloudinary.uploader

from .. import db
from ..models import User, Bot, Category, Product, Order, PriceTier, Cart, CartItem

api = Blueprint('api', __name__)

# --- CONFIGURATION & SETUP ---
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True
)
SERVER_URL = "https://telegram-bot-creator.onrender.com"
NOWPAYMENTS_API_KEY = os.environ.get('NOWPAYMENTS_API_KEY')
NOWPAYMENTS_IPN_SECRET_KEY = os.environ.get('NOWPAYMENTS_IPN_SECRET_KEY')

# --- HELPER FUNCTIONS ---
def run_async(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'message': 'Admin access is required for this action.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- TELEGRAM & PAYMENT FUNCTIONS ---
async def setup_bot_webhook(bot_token):
    logging.info(f"Setting up webhook for token: {bot_token[:10]}... ---")
    bot = telegram.Bot(token=bot_token)
    webhook_url = f"{SERVER_URL}/webhook/{bot_token}"
    try:
        await bot.set_webhook(webhook_url)
        logging.info(f"--- SUCCESS: Webhook set for {bot_token[:10]}... ---")
    except Exception as e:
        logging.error(f"--- ERROR: Failed to set webhook for {bot_token[:10]}. Reason: {e} ---")

def execute_payout(order):
    pass

async def send_cart_view(bot, chat_id, message_id, bot_id):
    cart = Cart.query.filter_by(chat_id=str(chat_id), bot_id=bot_id).first()
    if not cart or not cart.items:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Your shopping cart is empty.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]))
        return
    cart_text = "🛒 **Your Shopping Cart**\n\n"
    total_price = 0
    keyboard = []
    for item in cart.items:
        item_total = item.quantity * item.price_tier.price
        cart_text += f"- {item.quantity}x {item.price_tier.product.name} ({item.price_tier.label}) - £{item_total:.2f}\n"
        total_price += item_total
        keyboard.append([InlineKeyboardButton(f"❌ Remove {item.price_tier.label}", callback_data=f"remove_item:{item.id}")])
    cart_text += f"\n**Total: £{total_price:.2f}**"
    keyboard.append([InlineKeyboardButton("🗑️ Clear Cart", callback_data=f"clear_cart:{cart.id}")])
    keyboard.append([InlineKeyboardButton("✅ Checkout", callback_data=f"checkout:{cart.id}")])
    keyboard.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=cart_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_telegram_update(bot_token, update_data):
    logging.info(f"--- Handling update for bot token: {bot_token[:10]}... ---")
    bot = telegram.Bot(token=bot_token)
    update = telegram.Update.de_json(update_data, bot)
    with current_app.app_context():
        bot_data = Bot.query.filter_by(token=bot_token).first()
        if not bot_data or not bot_data.owner.is_active:
            return

        if update.callback_query:
            query = update.callback_query
            chat_id = query.message.chat_id
            message_id = query.message.message_id
            data = query.data
            await query.answer()
            
            parts = data.split(':')
            action = parts[0]
            item_id = parts[1] if len(parts) > 1 else None

            if action == 'main_menu':
                keyboard = [
                    [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
                    [InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
                    [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text=bot_data.welcome_message, reply_markup=reply_markup)

            elif action == 'browse_products':
                main_categories = [c for c in bot_data.categories if c.parent_id is None]
                if not main_categories:
                    await query.edit_message_text(text="This shop has no categories yet.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))
                    return
                keyboard = [[InlineKeyboardButton(c.name, callback_data=f"view_category:{c.id}")] for c in main_categories]
                keyboard.append([InlineKeyboardButton("🛒 View Cart", callback_data="view_cart"), InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text="Please select a category:", reply_markup=reply_markup)

            elif action == 'view_category':
                category = db.session.get(Category, item_id)
                if not category: return
                
                back_button_data = f"view_category:{category.parent_id}" if category.parent_id else "browse_products"
                
                if category.sub_categories:
                    keyboard = [[InlineKeyboardButton(sc.name, callback_data=f"view_category:{sc.id}")] for sc in category.sub_categories]
                    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=back_button_data), InlineKeyboardButton("🛒 View Cart", callback_data="view_cart"), InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(text=f"Sub-categories in {category.name}:", reply_markup=reply_markup)
                elif category.products:
                    await query.edit_message_text(text=f"Products in {category.name}:")
                    for product in category.products:
                        caption = f"**{product.name}**\n{product.description or ''}\n\n"
                        keyboard = []
                        for tier in product.price_tiers:
                            caption += f"- {tier.label}: £{tier.price}\n"
                            keyboard.append([InlineKeyboardButton(f"Add {tier.label} to Cart", callback_data=f"add_cart:{tier.id}")])
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        try:
                            if product.image_url:
                                await bot.send_photo(chat_id=chat_id, photo=product.image_url, caption=caption, reply_markup=reply_markup, parse_mode='Markdown')
                            else:
                                await bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup, parse_mode='Markdown')
                        except telegram.error.BadRequest:
                            await bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup, parse_mode='Markdown')
                    
                    nav_keyboard = [[
                        InlineKeyboardButton("⬅️ Back", callback_data=back_button_data),
                        InlineKeyboardButton("🛒 View Cart", callback_data="view_cart"),
                        InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
                    ]]
                    await bot.send_message(chat_id=chat_id, text="What would you like to do next?", reply_markup=InlineKeyboardMarkup(nav_keyboard))
                else:
                    await query.edit_message_text(text=f"No products or sub-categories found in {category.name}.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_button_data)]]))
            
            elif action == 'add_cart':
                price_tier = db.session.get(PriceTier, item_id)
                if price_tier:
                    cart = Cart.query.filter_by(chat_id=str(chat_id), bot_id=bot_data.id).first()
                    if not cart:
                        cart = Cart(chat_id=str(chat_id), bot_id=bot_data.id)
                        db.session.add(cart)
                        db.session.flush()
                    
                    cart_item = CartItem.query.filter_by(cart_id=cart.id, price_tier_id=price_tier.id).first()
                    if cart_item:
                        cart_item.quantity += 1
                    else:
                        cart_item = CartItem(cart_id=cart.id, price_tier_id=price_tier.id, quantity=1)
                        db.session.add(cart_item)
                    db.session.commit()
                    await bot.send_message(chat_id=chat_id, text=f"✅ '{price_tier.label}' for '{price_tier.product.name}' has been added to your cart.")

            elif action == 'view_cart':
                await send_cart_view(bot, chat_id, message_id, bot_data.id)

            elif action == 'remove_item':
                cart_item = db.session.get(CartItem, item_id)
                if cart_item:
                    db.session.delete(cart_item)
                    db.session.commit()
                await send_cart_view(bot, chat_id, message_id, bot_data.id)
            
            elif action == 'clear_cart':
                cart = db.session.get(Cart, item_id)
                if cart:
                    CartItem.query.filter_by(cart_id=cart.id).delete()
                    db.session.commit()
                await send_cart_view(bot, chat_id, message_id, bot_data.id)

            elif action == 'checkout':
                cart = db.session.get(Cart, item_id)
                if not cart or not cart.items:
                    await query.edit_message_text(text="Your cart is empty. Nothing to checkout.")
                    return
                
                total_price = sum(item.quantity * item.price_tier.price for item in cart.items)
                order_description = ", ".join([f"{item.quantity}x {item.price_tier.product.name} ({item.price_tier.label})" for item in cart.items])

                new_order = Order(
                    product_name=order_description, 
                    price=total_price, 
                    bot_id=cart.bot_id,
                    chat_id=str(chat_id),
                    telegram_username=query.from_user.username,
                    status='awaiting_payment'
                )
                db.session.add(new_order)
                db.session.commit()

                headers = {'x-api-key': NOWPAYMENTS_API_KEY}
                payload = {"price_amount": total_price, "price_currency": "usd", "order_id": new_order.id, "ipn_callback_url": f"{SERVER_URL}/webhook/nowpayments"}
                response = requests.post('https://api.nowpayments.io/v1/invoice', headers=headers, json=payload)
                
                if response.ok:
                    CartItem.query.filter_by(cart_id=cart.id).delete()
                    db.session.commit()
                    payment_data = response.json()
                    invoice_url = payment_data.get('invoice_url')
                    await query.edit_message_text(text=f"Thank you! Please complete your payment of £{total_price:.2f} using the secure link below:\n\n{invoice_url}")
                else:
                    await query.edit_message_text(text="Sorry, there was an error creating your payment link. Please try again.")
            
            elif action == 'my_orders':
                orders = Order.query.filter_by(chat_id=str(chat_id), bot_id=bot_data.id).order_by(Order.timestamp.desc()).limit(10).all()
                if not orders:
                    await query.edit_message_text(text="You have no past orders.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]))
                    return
                
                orders_text = "📦 **Your Recent Orders**\n\n"
                for order in orders:
                    status_text = order.status.replace('_', ' ').title()
                    orders_text += f"_{order.timestamp.strftime('%d %b %Y')}_ - {order.product_name}\n**Status:** {status_text}\n\n"
                
                await query.edit_message_text(text=orders_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]), parse_mode='Markdown')

        elif update.message and update.message.text:
            chat_id = update.message.chat_id
            text = update.message.text

            pending_order_address = Order.query.filter_by(bot_id=bot_data.id, status='awaiting_address', chat_id=str(chat_id)).first()
            if pending_order_address:
                pending_order_address.shipping_address = text
                pending_order_address.status = 'awaiting_note'
                db.session.commit()
                await bot.send_message(chat_id=chat_id, text="Great! Please reply with any additional notes for your order.")
                return

            pending_order_note = Order.query.filter_by(bot_id=bot_data.id, status='awaiting_note', chat_id=str(chat_id)).first()
            if pending_order_note:
                pending_order_note.customer_note = text
                pending_order_note.status = 'paid'
                db.session.commit()
                await bot.send_message(chat_id=chat_id, text="Thank you! Your order is complete and will be processed shortly.")
                return

            keyboard = [
                [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
                [InlineKeyboardButton("📦 My Orders", callback_data="my_orders")],
                [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot.send_message(chat_id=chat_id, text=bot_data.welcome_message, reply_markup=reply_markup)


# --- WEBHOOK ROUTES (Publicly Accessible) ---

@api.route('/webhook/<string:bot_token>', methods=['POST'])
def telegram_webhook(bot_token):
    run_async(handle_telegram_update(bot_token, request.get_json()))
    return "ok", 200

@api.route('/webhook/nowpayments', methods=['POST'])
def nowpayments_webhook():
    signature = request.headers.get('x-nowpayments-sig')
    if not signature or not NOWPAYMENTS_IPN_SECRET_KEY: return "Configuration error", 400
    try:
        sorted_payload = json.dumps(request.get_json(), sort_keys=True, separators=(',', ':')).encode('utf-8')
        expected_signature = hmac.new(NOWPAYMENTS_IPN_SECRET_KEY.encode('utf-8'), sorted_payload, hashlib.sha512).hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            return "Invalid signature", 400
    except Exception as e:
        return "Verification error", 400
    data = request.get_json()
    order_id = data.get('order_id')
    payment_status = data.get('payment_status')
    order = db.session.get(Order, order_id)
    if order and payment_status == 'finished' and order.status == 'awaiting_payment':
        order.status = 'awaiting_address'
        db.session.commit()
        bot = telegram.Bot(token=order.bot.token)
        run_async(bot.send_message(chat_id=order.chat_id, text="✅ Payment confirmed! Please reply with your full shipping address."))
        execute_payout(order)
    return "ok", 200

# --- AUTHENTICATION ROUTES ---

@api.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.is_active and user.check_password(data.get('password')):
        login_user(user)
        return jsonify({'message': 'Login successful!', 'userId': user.id}), 200
    return jsonify({'message': 'Invalid email or password'}), 401

@api.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful!'}), 200

@api.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.check_password(data.get('password')) and user.is_admin:
        login_user(user)
        return jsonify({'message': 'Admin login successful!'}), 200
    return jsonify({'message': 'Invalid admin credentials or permissions'}), 401

# --- CLIENT API ROUTES (ALL SECURED) ---

@api.route('/api/bots', methods=['POST'])
@login_required
def create_bot():
    data = request.get_json()
    bot_token = data.get('bot_token')
    if Bot.query.filter_by(token=bot_token).first():
        return jsonify({'message': 'A bot with this token already exists.'}), 409
    new_bot = Bot(token=bot_token, wallet=data.get('wallet_address'), user_id=current_user.id)
    db.session.add(new_bot)
    db.session.commit()
    run_async(setup_bot_webhook(bot_token))
    return jsonify(new_bot.to_dict()), 201

@api.route('/api/users/<string:user_id>/bots', methods=['GET'])
@login_required
def get_user_bots(user_id):
    if current_user.id != user_id:
        return jsonify({'message': 'Forbidden'}), 403
    return jsonify([bot.to_dict() for bot in current_user.bots])

@api.route('/api/users/<string:user_id>/dashboard-stats', methods=['GET'])
@login_required
def get_user_dashboard_stats(user_id):
    if current_user.id != user_id:
        return jsonify({'message': 'Forbidden'}), 403
    bot_ids = [bot.id for bot in current_user.bots]
    total_sales = db.session.query(db.func.sum(Order.price)).filter(Order.bot_id.in_(bot_ids)).scalar() or 0
    total_orders = Order.query.filter(Order.bot_id.in_(bot_ids)).count()
    recent_orders_query = Order.query.filter(Order.bot_id.in_(bot_ids)).order_by(Order.timestamp.desc()).limit(5).all()
    recent_orders = [order.to_dict() for order in recent_orders_query]
    stats = {'total_sales': round(total_sales, 2), 'total_orders': total_orders, 'recent_orders': recent_orders}
    return jsonify(stats)

@api.route('/api/bots/<string:bot_id>', methods=['GET'])
@login_required
def get_bot_details(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot or bot.owner != current_user:
        return jsonify({'message': 'Bot not found or access denied'}), 404
    return jsonify(bot.to_dict())

@api.route('/api/bots/<string:bot_id>', methods=['DELETE'])
@login_required
def delete_bot(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot or bot.owner != current_user:
        return jsonify({'message': 'Bot not found or access denied'}), 404
    db.session.delete(bot)
    db.session.commit()
    return jsonify({'message': 'Bot deleted successfully'}), 200

@api.route('/api/bots/<string:bot_id>/welcome-message', methods=['POST'])
@login_required
def update_welcome_message(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot or bot.owner != current_user:
        return jsonify({'message': 'Bot not found or access denied'}), 404
    data = request.get_json()
    bot.welcome_message = data.get('message', '')
    db.session.commit()
    return jsonify({'message': 'Welcome message updated successfully.'}), 200

@api.route('/api/bots/<string:bot_id>/categories', methods=['POST'])
@login_required
def create_category(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot or bot.owner != current_user:
        return jsonify({'message': 'Bot not found or access denied'}), 404
    data = request.get_json()
    new_category = Category(name=data.get('name'), bot_id=bot.id, parent_id=data.get('parent_id'))
    db.session.add(new_category)
    db.session.commit()
    return jsonify(new_category.to_dict()), 201

@api.route('/api/categories/<string:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if not category or category.bot.owner != current_user:
        return jsonify({'message': 'Category not found or access denied'}), 404
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted successfully'}), 200

@api.route('/api/bots/<string:bot_id>/products', methods=['POST'])
@login_required
def add_product_to_bot(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot or bot.owner != current_user:
        return jsonify({'message': 'Bot not found or access denied'}), 404
    data = request.get_json()
    category_id = data.get('category_id')
    category = db.session.get(Category, category_id)
    if not category or category.bot_id != bot.id:
        return jsonify({'message': 'Category not found or does not belong to this bot'}), 404
    new_product = Product(name=data.get('name'), description=data.get('description'), unit=data.get('unit'), image_url=data.get('image_url'), video_url=data.get('video_url'), category_id=category.id)
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201
    
@api.route('/api/products/<string:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product or product.category.bot.owner != current_user:
        return jsonify({'message': 'Product not found or access denied'}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'}), 200

@api.route('/api/products/<string:product_id>/price-tiers', methods=['POST'])
@login_required
def add_price_tier(product_id):
    product = db.session.get(Product, product_id)
    if not product or product.category.bot.owner != current_user:
        return jsonify({'message': 'Product not found or access denied'}), 404
    data = request.get_json()
    new_price_tier = PriceTier(label=data.get('label'), price=float(data.get('price')), product_id=product.id)
    db.session.add(new_price_tier)
    db.session.commit()
    return jsonify(new_price_tier.to_dict()), 201

@api.route('/api/price-tiers/<string:tier_id>', methods=['DELETE'])
@login_required
def delete_price_tier(tier_id):
    price_tier = db.session.get(PriceTier, tier_id)
    if not price_tier or price_tier.product.category.bot.owner != current_user:
        return jsonify({'message': 'Price tier not found or access denied'}), 404
    db.session.delete(price_tier)
    db.session.commit()
    return jsonify({'message': 'Price tier deleted successfully'}), 200

@api.route('/api/bots/<string:bot_id>/orders', methods=['GET'])
@login_required
def get_bot_orders(bot_id):
    bot = db.session.get(Bot, bot_id)
    if not bot or bot.owner != current_user:
        return jsonify({'message': 'Bot not found or access denied'}), 404
    return jsonify([o.to_dict() for o in bot.orders])

@api.route('/api/orders/<string:order_id>/dispatch', methods=['POST'])
@login_required
def dispatch_order(order_id):
    order = db.session.get(Order, order_id)
    if not order or order.bot.owner != current_user:
        return jsonify({'message': 'Order not found or access denied'}), 404
    order.status = 'dispatched'
    db.session.commit()
    return jsonify({'message': 'Order marked as dispatched'}), 200

@api.route('/api/upload-media', methods=['POST'])
@login_required
def upload_media():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    file_to_upload = request.files['file']
    if file_to_upload.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    try:
        upload_result = cloudinary.uploader.upload(file_to_upload, resource_type="auto")
        return jsonify({'secure_url': upload_result['secure_url']}), 200
    except Exception as e:
        logging.error(f"Cloudinary upload failed: {e}")
        return jsonify({'message': 'Failed to upload file.'}), 500

# --- ADMIN API ROUTES (ALL SECURED) ---

@api.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@api.route('/api/admin/users', methods=['POST'])
@admin_required
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

@api.route('/api/admin/users/<string:user_id>', methods=['GET'])
@admin_required
def get_user_details(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    return jsonify(user.to_dict())

@api.route('/api/admin/users/<string:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

@api.route('/api/admin/users/<string:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'message': f'User status changed to {user.is_active}'}), 200

@api.route('/api/admin/users/<string:user_id>/update-email', methods=['POST'])
@admin_required
def update_user_email(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    user.email = data.get('email')
    db.session.commit()
    return jsonify({'message': 'User email updated successfully'}), 200

@api.route('/api/admin/users/<string:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    user.set_password(data.get('password'))
    db.session.commit()
    return jsonify({'message': 'User password reset successfully'}), 200

@api.route('/api/admin/orders', methods=['GET'])
@admin_required
def get_all_orders():
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    orders_with_user_info = []
    for order in orders:
        order_data = order.to_dict()
        order_data['user_email'] = order.bot.owner.email
        orders_with_user_info.append(order_data)
    return jsonify(orders_with_user_info)

@api.route('/api/admin/dashboard-stats', methods=['GET'])
@admin_required
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
