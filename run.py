from app import create_app, db

app = create_app()

# This adds our custom "init-db" command to the Flask command-line interface.
# This is the most reliable way to run database commands in a live environment.
@app.cli.command("init-db")
def init_db_command():
    """Clears existing data and creates new tables."""
    db.create_all()
    print("Initialized the database.")

# This block is only for running the server on your local computer for testing.
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
