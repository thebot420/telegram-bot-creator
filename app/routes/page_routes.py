from flask import Blueprint, render_template

# --- THIS IS THE CRITICAL FIX ---
# We are now explicitly telling this Blueprint where to find its static files
# and that it should serve them from the main URL (e.g., /style.css).
pages = Blueprint(
    'pages', 
    __name__,
    template_folder='../templates',
    static_folder='../static',
    static_url_path='/'
)

@pages.route('/')
def serve_login_page():
    return render_template('index.html')

@pages.route('/dashboard.html')
def serve_dashboard():
    return render_template('dashboard.html')

@pages.route('/manage/<bot_id>')
def serve_manage_page(bot_id):
    return render_template('manage.html')

@pages.route('/orders/<bot_id>')
def serve_orders_page(bot_id):
    return render_template('orders.html')

@pages.route('/admin')
def serve_admin_login_page():
    return render_template('admin.html')

@pages.route('/admin/dashboard')
def serve_admin_dashboard():
    return render_template('admin_main_dashboard.html')

@pages.route('/admin/users')
def serve_admin_users_page():
    return render_template('admin_users.html')

@pages.route('/admin/users/<user_id>')
def serve_user_details_page(user_id):
    return render_template('admin_user_details.html')

@pages.route('/admin/orders')
def serve_master_orders_page():
    return render_template('admin_orders.html')
