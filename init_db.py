from backend.database import db
from backend.models import User, Doctor
from werkzeug.security import generate_password_hash
from app import app  # Make sure app is imported after db and models

with app.app_context():
    # Create tables
    db.create_all()

    # Optional: seed with an admin user
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
