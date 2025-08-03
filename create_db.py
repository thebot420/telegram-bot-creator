# This script's only job is to create the database tables.
# It is designed to be run by the Render build process.

from app import app, db
import logging

logging.basicConfig(level=logging.INFO)

logging.info("--- Starting database creation script ---")
# We create an application context to work with the database
with app.app_context():
    logging.info("--- Creating all database tables... ---")
    db.create_all()
    logging.info("--- Database tables created successfully. ---")

