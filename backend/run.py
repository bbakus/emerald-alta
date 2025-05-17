from app import create_app

app = create_app()

if __name__ == "__main__":
    # Use Flask's development server for local development
    app.run(debug=True)
    
# To run with gunicorn: gunicorn -w 4 -b 127.0.0.1:5000 run:app
# This provides better database connection management with multiple workers 