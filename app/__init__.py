from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    """
    This is the application factory. It creates and configures the Flask app.
    """
    # This explicitly tells Flask where to find the frontend files.
    app = Flask(__name__, instance_relative_config=True)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/bots.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy knows about our tables.
        from . import models

        # Import and register Blueprints (our route files).
        from .routes.page_routes import pages
        from .routes.api_routes import api
        app.register_blueprint(pages)
        app.register_blueprint(api)

        return app
