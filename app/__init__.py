from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager() # Create the manager instance here

def create_app():
    """
    This is the application factory. It creates and configures the Flask app.
    """
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='templates', 
                static_folder='static')

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a-dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/bots.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # --- Initialize Extensions ---
    db.init_app(app)
    login_manager.init_app(app) # Initialize it with the app

    # This user_loader function is used by Flask-Login to reload the user object
    # from the user ID stored in the session.
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(user_id)

    with app.app_context():
        # Import and register Blueprints
        from .routes.page_routes import pages
        from .routes.api_routes import api
        app.register_blueprint(pages)
        app.register_blueprint(api)

        return app