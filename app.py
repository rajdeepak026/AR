import os
from flask import Flask, send_from_directory
from backend.database import db
from datetime import timedelta
from dotenv import load_dotenv  # ✅ Load .env variables for local dev

# ✅ Load .env file (useful for local testing)
load_dotenv()

app = Flask(__name__)

# Google verification route (static file)
@app.route('/google0bd79030d3228202.html')
def google_verification():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'google0bd79030d3228202.html')

# ✅ Production-ready database config (uses PostgreSQL from Render or fallback to SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///med.sqlite3"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ Secret key from environment (NEVER hardcode in production)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-fallback-dev-secret-key-if-not-set")

# ✅ Session lifetime config
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# ✅ Initialize database
db.init_app(app)

# ✅ App context for importing routes & optionally creating tables
with app.app_context():
    from backend import controllers

    # Uncomment only for the first time (create tables in Render DB)
    # db.create_all()

# ✅ Main entry point with debug controlled by env variable
if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "True")
