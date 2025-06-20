import os
from flask import Flask, send_from_directory
from backend.database import db
from datetime import timedelta
from dotenv import load_dotenv

# ✅ Load environment variables from .env file (for local dev)
load_dotenv()

app = Flask(__name__)

# Google verification route (static file)
@app.route('/google0bd79030d3228202.html')
def google_verification():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'google0bd79030d3228202.html')

# ✅ PostgreSQL database config (no SQLite fallback)
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise ValueError("❌ DATABASE_URL is not set in environment variables!")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ Secret key for sessions (required)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback-secret")

# ✅ Session lifetime
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# ✅ Initialize DB
db.init_app(app)

# ✅ App context to import routes
with app.app_context():
    from backend import controllers
    # Optional: Uncomment below for one-time table creation
    # db.create_all()

# ✅ Entry point
if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "True")
