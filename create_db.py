# This script's only job is to create the database tables.
# It is designed to be run by the Render build process.

from app import create_app, db
import logging

logging.basicConfig(level=logging.INFO)

logging.info("--- Starting database creation script ---")
# We create an instance of our app to establish the context
app = create_app()
with app.app_context():
    logging.info("--- Creating all database tables... ---")
    db.create_all()
    logging.info("--- Database tables created successfully. ---")

