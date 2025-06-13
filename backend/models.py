# models.py

from .database import db
import datetime

class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    fullName = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    age = db.Column(db.Integer(), nullable=False)
    phone = db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), nullable=False)
    password = db.Column(db.String(),nullable=False)
    type = db.Column(db.String(), default="general")

    # Define relationship to appointments where this user is the patient
    appointments = db.relationship('Appointment', backref='patient', lazy=True, primaryjoin="User.id == Appointment.user_id")

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)   # Hashed
    status = db.Column(db.String(20), nullable=False, default='pending')     # 'pending' or 'approved'
    photo = db.Column(db.String(200))     # Path to uploaded photo
    age = db.Column(db.Integer(), nullable=True)     # Added age field
    address = db.Column(db.String(200), nullable=True) # Added address field

    # Existing fields for general doctor availability (HH:MM format)
    available_from = db.Column(db.String(5), nullable=True)
    available_to = db.Column(db.String(5), nullable=True)

    # NEW fields for specific availability slots from the HTML form
    morning_slot = db.Column(db.String(50), nullable=True) # Store full slot description
    afternoon_slot = db.Column(db.String(50), nullable=True) # Store full slot description
    evening_slot = db.Column(db.String(50), nullable=True) # Store full slot description

    # Define relationship to appointments where this doctor is involved
    appointments = db.relationship('Appointment', backref='doctor', lazy=True, primaryjoin="Doctor.id == Appointment.doctor_id")

    def __repr__(self):
        return f"<Doctor {self.full_name}>"

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    appointment_time = db.Column(db.String(10), nullable=False, default="09:00 AM") # e.g., "10:30 AM"
    symptoms = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # 'pending', 'confirmed', 'rejected', 'cancelled', 'completed'
    token_number = db.Column(db.String(10), nullable=True) # Optional token number
    
    # This new field will automatically store the creation timestamp
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Appointment {self.id} for User {self.user_id} with Doctor {self.doctor_id}>"