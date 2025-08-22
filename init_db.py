# init_db.py
import datetime
from flask import Flask
from backend.database import db
from backend.models import User, Doctor, Appointment

# ✅ Setup a temporary Flask app for database initialization
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"  # Always local SQLite
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    print("🔄 Creating database and tables...")
    db.drop_all()   # ⚠️ Clears old tables (remove if you want to keep data)
    db.create_all()

    print("✅ Inserting dummy data...")

    # -------------------
    # Dummy User
    # -------------------
    if not User.query.filter_by(email="johndoe@example.com").first():
        user = User(
            fullName="John Doe",
            email="johndoe@example.com",
            age=30,
            phone="1234567890",
            address="123 Main Street",
            password="hashed_password",  # TODO: hash properly in production
            type="general"
        )
        db.session.add(user)
        print("👤 Dummy user added")

    # -------------------
    # Dummy Admin
    # -------------------
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(
            fullName="Admin User",
            email="admin@example.com",
            age=35,
            phone="0000000000",
            address="Admin Headquarters",
            password="admin_password",  # TODO: hash properly
            type="admin"
        )
        db.session.add(admin)
        print("🛠️ Dummy admin added")

    # -------------------
    # Dummy Doctor
    # -------------------
    if not Doctor.query.filter_by(email="alice@example.com").first():
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
        db.session.add(doctor)
        print("👩‍⚕️ Dummy doctor added")

    db.session.commit()

    # -------------------
    # Dummy Appointment
    # -------------------
    if not Appointment.query.first():  # Only add if no appointment exists
        appointment = Appointment(
            user_id=1,
            doctor_id=1,
            appointment_date=datetime.date.today(),
            appointment_time="10:30 AM",
            symptoms="Chest pain and shortness of breath",
            status="pending",
            token_number="A001"
        )
        db.session.add(appointment)
        print("📅 Dummy appointment added")

    db.session.commit()

    print("🎉 Dummy data inserted successfully!")
