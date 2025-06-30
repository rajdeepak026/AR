# models.py

from .database import db
import datetime

class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    fullName = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    age = db.Column(db.Integer(), nullable=False)
    phone = db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), nullable=False)
    password = db.Column(db.String(), nullable=False)
    type = db.Column(db.String(), default="general")
    fcm_token = db.Column(db.Text)  # this stores the OneSignal player ID

    appointments = db.relationship('Appointment', backref='patient', lazy=True, primaryjoin="User.id == Appointment.user_id")

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending' or 'approved'
    photo = db.Column(db.String(200))
    age = db.Column(db.Integer(), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    fcm_token = db.Column(db.Text)

    available_from = db.Column(db.String(5), nullable=True)
    available_to = db.Column(db.String(5), nullable=True)

    morning_slot = db.Column(db.String(50), nullable=True)
    afternoon_slot = db.Column(db.String(50), nullable=True)
    evening_slot = db.Column(db.String(50), nullable=True)

    # 🔥 NEW FIELD: Clinic status
    clinic_status = db.Column(db.String(10), nullable=False, default='open')  # 'open' or 'closed'

    appointments = db.relationship('Appointment', backref='doctor', lazy=True, primaryjoin="Doctor.id == Appointment.doctor_id")

    def __repr__(self):
        return f"<Doctor {self.full_name}>"

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    appointment_time = db.Column(db.String(100), nullable=False, default="09:00 AM")
    symptoms = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    token_number = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Appointment {self.id} for User {self.user_id} with Doctor {self.doctor_id}>"
