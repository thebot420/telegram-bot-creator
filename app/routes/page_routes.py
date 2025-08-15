from flask import Blueprint, render_template
from flask_login import login_required, current_user

# We need a way to check if a user is an admin here too.
# A simple check is enough for page routes.
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            # Redirect to a non-admin page or show an error
            return "Admin access required.", 403
        return f(*args, **kwargs)
    return decorated_function


pages = Blueprint(
    'pages', 
    __name__,
    template_folder='../templates',
    static_folder='../static',
    static_url_path='/'
)

# --- Public Routes ---
@pages.route('/')
def serve_login_page():
    return render_template('index.html')

@pages.route('/admin')
def serve_admin_login_page():
    return render_template('admin.html')

# --- User Routes (Require Login) ---
@pages.route('/dashboard.html')
@login_required
def serve_dashboard():
    return render_template('dashboard.html')

@pages.route('/manage/<string:bot_id>')
@login_required
def serve_manage_page(bot_id):
    return render_template('manage.html')

@pages.route('/orders/<string:bot_id>')
@login_required
def serve_orders_page(bot_id):
    return render_template('orders.html')

# --- Admin Routes (Require Admin Login) ---
@pages.route('/admin/dashboard')
@login_required
@admin_required
def serve_admin_dashboard():
    return render_template('admin_main_dashboard.html')

@pages.route('/admin/users')
@login_required
@admin_required
def serve_admin_users_page():
    return render_template('admin_users.html')

@pages.route('/admin/users/<string:user_id>')
@login_required
@admin_required
def serve_user_details_page(user_id):
    return render_template('admin_user_details.html')

@pages.route('/admin/orders')
@login_required
@admin_required
def serve_master_orders_page():
    return render_template('admin_orders.html')