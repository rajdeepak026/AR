from backend.database import db
from backend.models import User, Doctor
from werkzeug.security import generate_password_hash
from app import app  # This must be after importing db/models
from dotenv import load_dotenv
import os

# ✅ Load environment variables explicitly from the correct path
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

if __name__ == "__main__":
    with app.app_context():
        # ✅ Confirm that environment variable is loaded
        print("📦 DATABASE_URL:", os.getenv("DATABASE_URL"))

        print("🔄 Connecting to the database...")
        try:
            db.create_all()
            print("✅ Tables checked/created successfully.")
        except Exception as e:
            print("❌ Failed to connect or create tables:", str(e))
            exit(1)

        # ✅ Admin creation logic
        admin_email = "admin@gmail.com"
        admin_exists = User.query.filter_by(email=admin_email).first()

        if not admin_exists:
            admin_user = User(
                fullName="Admin",
                email=admin_email,
                age=30,
                phone="9999999999",
                address="Admin Street",
                password=generate_password_hash("admin123"),
                type="admin"
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully in Render DB.")
        else:
            print("ℹ️ Admin user already exists in Render DB.")
