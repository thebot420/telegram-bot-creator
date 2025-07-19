# This script is dedicated to creating the database tables.
# It will be run by Render during the build process.

from app import app, db
import logging

logging.basicConfig(level=logging.INFO)

logging.info("--- Starting database creation script ---")

# The app_context is necessary for SQLAlchemy to know about the application
# and the database URI.
with app.app_context():
    logging.info("--- Creating all database tables... ---")
    db.create_all()
    logging.info("--- Database tables created successfully. ---")

