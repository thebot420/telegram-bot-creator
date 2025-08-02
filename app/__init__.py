from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# --- THIS IS THE CRITICAL FIX ---
# Get the absolute path of the directory where this __init__.py file lives.
# This gives us a reliable starting point.
basedir = os.path.abspath(os.path.dirname(__file__))

db = SQLAlchemy()

def create_app():
    """
    This is the application factory. It creates and configures the Flask app.
    """
    # Create the Flask app instance.
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    # We now explicitly tell Flask the absolute paths to the template and static folders.
    # This removes any guesswork for the server.
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(basedir, '../instance/bots.db')}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TEMPLATE_FOLDER=os.path.join(basedir, 'templates'),
        STATIC_FOLDER=os.path.join(basedir, 'static')
    )
    
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
