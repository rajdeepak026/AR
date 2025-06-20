from backend.database import db
from backend.models import User
from werkzeug.security import generate_password_hash
from app import app  # Import app last to avoid circular imports
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def reset_database():
    with app.app_context():
        print("📦 DATABASE_URL:", os.getenv("DATABASE_URL"))

        try:
            print("⚠️ Dropping all existing tables...")
            db.drop_all()

            print("✅ Creating new tables...")
            db.create_all()

            # Create admin user
            admin_email = "admin@gmail.com"
            if not User.query.filter_by(email=admin_email).first():
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
                print("✅ Admin user created.")
            else:
                print("ℹ️ Admin user already exists.")
        except Exception as e:
            print("❌ Error while resetting database:", e)

if __name__ == "__main__":
    reset_database()
