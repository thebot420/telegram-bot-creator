from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    """
    This is the application factory. It creates and configures the Flask app.
    """
    # --- THIS IS THE CRITICAL FIX ---
    # We are now explicitly telling Flask where to find our frontend files,
    # relative to the 'app' directory where this file lives.
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='templates', 
                static_folder='static')

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/bots.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy knows about our tables.
        from . import models

        # Import and register Blueprints
        from .routes.page_routes import pages
        from .routes.api_routes import api
        app.register_blueprint(pages)
        app.register_blueprint(api)

        return app
