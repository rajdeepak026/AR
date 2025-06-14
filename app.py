import os
from flask import Flask, send_from_directory
from backend.database import db
from datetime import timedelta # Added: Import timedelta for session lifetime

app = Flask(__name__)
@app.route('/google0bd79030d3228202.html')
def google_verification():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'google0bd79030d3228202.html')

# --- CHANGE 1: Database Configuration for Production ---
# Use a production-ready database (e.g., PostgreSQL, MySQL)
# and load the URI from an environment variable
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///med.sqlite3")
# The second argument to .get() is a fallback for local development if DATABASE_URL isn't set.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- CHANGE 2: Secret Key (CRITICAL SECURITY) ---
# Load your secret key from an environment variable.
# NEVER hardcode it in production.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-fallback-dev-secret-key-if-not-set")

# --- ADDITION: Configure Permanent Sessions ---
# Sessions will last for 30 days if marked as permanent
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

db.init_app(app)

# Import routes after app and db are set up
with app.app_context():
    from backend import controllers
    # --- OPTIONAL: Database Creation on First Run (less common for production) ---
    # db.create_all() # Only use this if you want tables to be created on app startup
                        # For production, use migration tools like Alembic.

if __name__ == "__main__":
    # --- CHANGE 3: Remove debug=True for Production (CRITICAL SECURITY & Performance) ---
    # app.run(debug=True) is ONLY for development.
    # In production, you will use a WSGI server like Gunicorn or uWSGI.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "True") # Use env var for debug mode
