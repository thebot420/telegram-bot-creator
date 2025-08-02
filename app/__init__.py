from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///bots.db')
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
