from app import create_app, db

app = create_app()

# NEW: This adds a custom command to our application.
# We can now run "flask init-db" from the command line.
@app.cli.command("init-db")
def init_db_command():
    """Clears the existing data and creates new tables."""
    db.create_all()
    print("Initialized the database.")

# This block is for running the server on your local computer for testing.
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
