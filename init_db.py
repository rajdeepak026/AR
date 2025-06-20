from backend.database import db
from backend.models import User, Doctor
from werkzeug.security import generate_password_hash
from app import app  # Import app after db/models to avoid circular import

# Ensure this runs only when script is executed directly
if __name__ == "__main__":
    with app.app_context():
        # ✅ Create tables if they don’t exist
        db.create_all()

        # ✅ Add admin user if not already present
        if not User.query.filter_by(email="admin@gmail.com").first():
            admin_user = User(
                fullName="Admin",
                email="admin@gmail.com",
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
