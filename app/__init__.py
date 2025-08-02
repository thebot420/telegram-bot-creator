from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Get the absolute path of the directory where this __init__.py file lives.
# This gives us a reliable starting point.
basedir = os.path.abspath(os.path.dirname(__file__))

db = SQLAlchemy()

def create_app():
    """
    This is the application factory. It creates and configures the Flask app.
    """
    # Create the Flask app instance.
    # We now explicitly tell Flask the absolute paths to the template and static folders.
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder=os.path.join(basedir, 'templates'), 
                static_folder=os.path.join(basedir, 'static'))

    # Configuration
    # Use the instance folder for the local SQLite database
    instance_path = os.path.join(os.path.dirname(basedir), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(instance_path, 'bots.db')}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy knows about them
        from . import models

        # Import and register Blueprints
        from .routes.page_routes import pages
        from .routes.api_routes import api
        app.register_blueprint(pages)
        app.register_blueprint(api)

        return app
