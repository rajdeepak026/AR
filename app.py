import os
from flask import Flask, send_from_directory
from backend.database import db
from datetime import timedelta
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask import Flask, send_from_directory


# ✅ Load environment variables from .env file
load_dotenv()

# ✅ Initialize Flask app
app = Flask(__name__)

@app.route('/sitemap.xml', endpoint='sitemap_static')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')
# ✅ Google verification route
@app.route('/google0bd79030d3228202.html')
def google_verification():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'google0bd79030d3228202.html')

# ✅ PostgreSQL configuration
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise ValueError("❌ DATABASE_URL is not set in environment variables!")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ Session configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback-secret")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# ✅ Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)  # 🔥 Add Flask-Migrate here

# ✅ Import routes inside app context
with app.app_context():
    from backend import controllers
    # db.create_all()  # Optional: only for first-time table creation

# ✅ Run app
if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "True")
