    from app import create_app, db

    app = create_app()

    # This adds our custom "init-db" command to the Flask CLI.
    @app.cli.command("init-db")
    def init_db_command():
        """Creates the database tables."""
        db.create_all()
        print("Initialized the database.")

    # This block is only for running the server on your local computer.
    if __name__ == '__main__':
        with app.app_context():
            db.create_all()
        app.run(host='0.0.0.0', port=5000, debug=True)
    