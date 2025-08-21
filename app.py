import os
from flask import Flask, send_from_directory
from backend.database import db
from datetime import timedelta
from dotenv import load_dotenv
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__, static_folder='static')

# ✅ Static routes
@app.route('/sitemap.xml', endpoint='sitemap_static')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/google0bd79030d3228202.html')
def google_verification():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'google0bd79030d3228202.html')


# ✅ Database config
use_sqlite = os.environ.get("USE_SQLITE") == "True"   # toggle with env var

database_url = None if use_sqlite else os.environ.get("DATABASE_URL")

# Fix old postgres:// URLs → postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Fall back to SQLite if no database_url
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ✅ Sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_NAME"] = "yourdr_session"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"


# ✅ Init extensions
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    from backend import controllers
    # db.create_all()  # Uncomment only if not using migrations


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "True")
