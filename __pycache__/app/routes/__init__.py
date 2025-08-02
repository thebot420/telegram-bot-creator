from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# 1. Initialize the database extension. 
# We create it here, but we will connect it to our app inside the factory.
db = SQLAlchemy()

def create_app():
    """
    This is the application factory function. It creates, configures, 
    and returns the Flask application instance.
    """
    # 2. Create the Flask app instance.
    # The 'instance_relative_config=True' allows for configuration files 
    # that are outside the main app package, which is good practice.
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    # 3. Configure the database. It will use your live Render database URL if the 
    # environment variable is set, otherwise it will fall back to a local 
    # 'bots.db' file for testing on your computer.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///bots.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 4. Connect the database extension to our newly created app.
    db.init_app(app)

    # 5. We need to run the next steps within the "application context"
    # so that Flask knows which app we're working with.
    with app.app_context():
        # Import the database models so SQLAlchemy knows about our tables.
        from . import models

        # Import and register the Blueprints (our new, separated route files).
        from .routes.page_routes import pages
        from .routes.api_routes import api
        app.register_blueprint(pages)
        app.register_blueprint(api)

        # 6. Return the fully configured application.
        return app
