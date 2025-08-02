from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# 1. Initialize the database extension.
db = SQLAlchemy()

def create_app():
    """
    This is the application factory. It creates and configures the Flask app.
    """
    # 2. Create the Flask app instance.
    # We explicitly tell Flask where to find the templates and static files.
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='templates', 
                static_folder='static')

    # --- Configuration ---
    # 3. Configure the database.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///bots.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 4. Connect the database extension to our app.
    db.init_app(app)

    with app.app_context():
        # 5. Import the models so SQLAlchemy knows about our tables.
        from . import models

        # 6. Import and register the Blueprints (our route files).
        from .routes.page_routes import pages
        from .routes.api_routes import api
        app.register_blueprint(pages)
        app.register_blueprint(api)

        # 7. Return the fully configured application.
        return app
