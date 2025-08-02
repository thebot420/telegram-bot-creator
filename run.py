from app import create_app, db

app = create_app()

# This block is only for running the server on your local computer for testing.
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
