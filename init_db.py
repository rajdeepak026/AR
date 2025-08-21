import datetime
from backend.database import db
from backend.models import User, Doctor, Appointment
from flask import Flask

# ✅ Setup a temporary Flask app for database initialization
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    print("🔄 Creating database and tables...")
    db.drop_all()   # ⚠️ Clears old tables (optional, remove if you want to keep data)
    db.create_all()

    print("✅ Inserting dummy data...")

    # Create dummy user
    user = User(
        fullName="John Doe",
        email="johndoe@example.com",
        age=30,
        phone="1234567890",
        address="123 Main Street",
        password="hashed_password",  # Ideally hash in production
        type="general"
    )

    # Create dummy doctor
    doctor = Doctor(
        full_name="Dr. Alice Smith",
        email="alice@example.com",
        phone="9876543210",
        specialty="Cardiology",
        password="hashed_password",
        status="approved",
        age=40,
        address="456 Clinic Ave",
        clinic_status="open"
    )

    # Create dummy appointment
    appointment = Appointment(
        user_id=1,
        doctor_id=1,
        appointment_date=datetime.date.today(),
        appointment_time="10:30 AM",
        symptoms="Chest pain and shortness of breath",
        status="pending",
        token_number="A001"
    )

    # Add to session
    db.session.add(user)
    db.session.add(doctor)
    db.session.add(appointment)
    db.session.commit()

    print("🎉 Dummy data inserted successfully!")
