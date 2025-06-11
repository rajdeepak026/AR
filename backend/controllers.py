from flask import render_template, redirect, request, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Doctor, Appointment
from .database import db
from flask import current_app as app
import datetime

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullName = request.form["fullName"]
        email = request.form["email"]
        age = request.form["age"]
        phone = request.form["phone"]
        address = request.form["address"]
        password = generate_password_hash(request.form["password"])

        new_user = User(
            fullName=fullName,
            email=email,
            age=age,
            phone=phone,
            address=address,
            password=password
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!", "success")
            return redirect(url_for("login_page"))
        except Exception:
            db.session.rollback()
            flash("Email or name already registered", "danger")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_type"] = user.type
            session["user_name"] = user.fullName

            if user.type == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.type == "general":
                return redirect(url_for("user_dashboard", user_id=user.id))

        doctor = Doctor.query.filter_by(email=email).first()
        if doctor and check_password_hash(doctor.password, password):
            if doctor.status != "approved":
                flash("Doctor account not approved yet.", "warning")
                return redirect(url_for("login_page"))

            session["user_id"] = doctor.id
            session["user_type"] = "doctor"
            session["user_name"] = doctor.full_name
            return redirect(url_for("doctor_dashboard", user_id=doctor.id))

        flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login_page"))

@app.route("/doctor_dashboard/<int:user_id>")
def doctor_dashboard(user_id):
    doctor = Doctor.query.get_or_404(user_id)
    # Ensure the user ID in the URL matches the session ID for the logged-in doctor
    if session.get("user_type") != "doctor" or session.get("user_id") != doctor.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))
    # Fetch appointments for this doctor, ordered by date and time
    doctor_appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    return render_template("doctor/doctor_dashboard.html", doctor=doctor, appointments=doctor_appointments)

@app.route("/doctor/appointments/<int:user_id>")
def doctor_appointments(user_id):
    """
    Route for doctor to manage all their appointments.
    """
    doctor = Doctor.query.get_or_404(user_id)
    # Ensure the user ID in the URL matches the session ID for the logged-in doctor
    if session.get("user_type") != "doctor" or session.get("user_id") != doctor.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    # Fetch appointments for this doctor, ordered by date and time
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    return render_template("doctor/doctor_appointments.html", appointments=appointments)


@app.route("/doctor/appointments/confirm/<int:appointment_id>")
def confirm_appointment_by_doctor(appointment_id):
    """
    Doctor route to confirm a pending appointment.
    """
    if session.get("user_type") != "doctor":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Ensure the doctor is confirming their own appointment
    if appointment.doctor_id != session.get("user_id"):
        flash("You can only confirm appointments assigned to you.", "danger")
        return redirect(url_for("doctor_dashboard", user_id=session.get("user_id")))

    if appointment.status == 'pending':
        appointment.status = "confirmed"
        # Generate a more unique token
        appointment.token_number = f"TKN{appointment_id}-{datetime.datetime.now().strftime('%H%M%S')}"

        try:
            db.session.commit()
            flash(f"Appointment {appointment_id} for {appointment.patient.fullName} confirmed.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error confirming appointment: {e}", "danger")
    else:
        flash(f"Appointment {appointment_id} is already '{appointment.status}'. Cannot confirm.", "warning")
    return redirect(url_for("doctor_dashboard", user_id=session.get("user_id")))


@app.route("/doctor/appointments/cancel/<int:appointment_id>")
def cancel_appointment_by_doctor(appointment_id):
    """
    Doctor route to cancel a pending or confirmed appointment.
    """
    if session.get("user_type") != "doctor":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Ensure the doctor is cancelling their own appointment
    if appointment.doctor_id != session.get("user_id"):
        flash("You can only cancel appointments assigned to you.", "danger")
        return redirect(url_for("doctor_dashboard", user_id=session.get("user_id")))

    if appointment.status in ['pending', 'confirmed']:
        appointment.status = "cancelled" # Changed status to 'cancelled' for doctor actions
        try:
            db.session.commit()
            flash(f"Appointment {appointment_id} for {appointment.patient.fullName} cancelled.", "warning")
        except Exception as e:
            db.session.rollback()
            flash(f"Error cancelling appointment: {e}", "danger")
    else:
        flash(f"Appointment {appointment_id} is already '{appointment.status}'. Cannot cancel.", "warning")
    return redirect(url_for("doctor_dashboard", user_id=session.get("user_id")))


@app.route("/doctor/profile/<int:user_id>", methods=["GET", "POST"])
def doctor_profile(user_id):
    """
    Doctor route to view and update their profile.
    """
    doctor = Doctor.query.get_or_404(user_id)
    # Ensure the user ID in the URL matches the session ID for the logged-in doctor
    if session.get("user_type") != "doctor" or session.get("user_id") != doctor.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    if request.method == "POST":
        doctor.full_name = request.form["full_name"]
        doctor.email = request.form["email"]
        doctor.phone = request.form["phone"]
        doctor.specialty = request.form["specialty"]
        # Removed lines attempting to update doctor.age and doctor.address
        # doctor.age = request.form.get("age", type=int)
        # doctor.address = request.form.get("address")

        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("doctor_profile", user_id=doctor.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", "danger")
            app.logger.error(f"Error updating doctor profile: {e}")

    return render_template("doctor/doctor_profile.html", doctor=doctor)


@app.route("/user_dashboard/<int:user_id>")
def user_dashboard(user_id):
    user = User.query.get_or_404(user_id)
    if session.get("user_type") != "general" or session.get("user_id") != user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))
    return render_template("user/user_dashboard.html", user=user)

@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    total_users = User.query.count()
    total_doctors = Doctor.query.count()
    todays_appointments = 0
    total_revenue = 0

    return render_template(
        "admin/admin_dashboard.html",
        user_name=session.get("user_name"),
        total_users=total_users,
        total_doctors=total_doctors,
        todays_appointments=todays_appointments,
        total_revenue=total_revenue
    )

@app.route("/manage_doctors")
def manage_doctors():
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    doctors = Doctor.query.all()
    return render_template("admin/manage_doctors.html", doctors=doctors)

@app.route("/manage_users")
def manage_users():
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    users = User.query.filter(User.type != 'admin').all()
    return render_template("admin/manage_users.html", users=users)

@app.route("/appointments")
def appointments():
    """
    Route for admin to manage all appointments.
    Fetches all appointments and displays them.
    """
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    # Fetch all appointments, ordered by date and time, and include doctor/user details
    all_appointments = Appointment.query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

    return render_template("admin/appointments.html", appointments=all_appointments)


@app.route("/admin/appointments/approve/<int:appointment_id>")
def approve_appointment(appointment_id):
    """
    Admin route to approve a pending appointment.
    """
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.status == 'pending':
        appointment.status = "confirmed"
        # Optional: Assign a token number if confirmed
        # For simplicity, generating a basic token here. You might have more complex logic.
        # Ensure your Appointment model can store this.
        # For example, generate a simple incrementing token or random one.
        appointment.token_number = f"TKN{appointment_id}" # Simple token

        try:
            db.session.commit()
            flash(f"Appointment {appointment.id} for {appointment.patient.fullName} with Dr. {appointment.doctor.full_name} approved and confirmed.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error approving appointment: {e}", "danger")
    else:
        flash(f"Appointment {appointment.id} is already '{appointment.status}'. Cannot approve.", "warning")
    return redirect(url_for("appointments")) # Redirect back to appointments list

@app.route("/admin/appointments/reject/<int:appointment_id>")
def reject_appointment(appointment_id):
    """
    Admin route to reject a pending appointment.
    """
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.status == 'pending':
        appointment.status = "rejected"
        try:
            db.session.commit()
            flash(f"Appointment {appointment.id} for {appointment.patient.fullName} with Dr. {appointment.doctor.full_name} rejected.", "warning")
        except Exception as e:
            db.session.rollback()
            flash(f"Error rejecting appointment: {e}", "danger")
    else:
        flash(f"Appointment {appointment.id} is already '{appointment.status}'. Cannot reject.", "warning")
    return redirect(url_for("appointments")) # Redirect back to appointments list


@app.route("/add_doctor", methods=["GET", "POST"])
def add_doctor():
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        specialty = request.form["specialty"]
        password = generate_password_hash(request.form["password"])

        new_doctor = Doctor(
            full_name=full_name,
            email=email,
            phone=phone,
            specialty=specialty,
            password=password,
            status='pending'
        )

        try:
            db.session.add(new_doctor)
            db.session.commit()
            flash("Doctor added successfully and is pending approval.", "success")
            return redirect(url_for("manage_doctors"))
        except Exception:
            db.session.rollback()
            flash("Email already in use or another error occurred.", "danger")

    return render_template("admin/adddoctor.html")

@app.route("/approve_doctor/<int:doctor_id>")
def approve_doctor(doctor_id):
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.status = "approved"
    db.session.commit()
    flash(f"Doctor {doctor.full_name} approved.", "success")
    return redirect(url_for("manage_doctors"))

@app.route("/reject_doctor/<int:doctor_id>")
def reject_doctor(doctor_id):
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.status = "rejected"
    db.session.commit()
    flash(f"Doctor {doctor.full_name} rejected.", "warning")
    return redirect(url_for("manage_doctors"))

# --- User-Specific Routes (keeping for context, assuming these are complete) ---
@app.route("/user/search_doctors", methods=["GET"])
def search_doctors():
    if session.get("user_type") != "general":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))
    doctors_query = Doctor.query.filter_by(status='approved')
    all_approved_doctors = Doctor.query.filter_by(status='approved').all()
    specialties = sorted(list(set([d.specialty for d in all_approved_doctors])))
    specialty_filter = request.args.get("specialty")
    location_filter = request.args.get("location")
    if specialty_filter and specialty_filter != "Choose...":
        doctors_query = doctors_query.filter_by(specialty=specialty_filter)
    if location_filter:
        flash("Location search is not fully implemented yet, searching by specialty only.", "info")
    doctors = doctors_query.all()
    return render_template(
        "user/search_doctors.html",
        doctors=doctors,
        specialties=specialties,
        selected_specialty=specialty_filter if specialty_filter else "Choose...",
        selected_location=location_filter if location_filter else ""
    )

@app.route("/user/book_appointment", methods=["GET", "POST"])
def book_appointment():
    if session.get("user_type") != "general":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))
    user_id = session.get("user_id")
    current_user = User.query.get_or_404(user_id)
    doctor_id = request.args.get('doctor_id', type=int)
    selected_doctor = None
    if doctor_id:
        selected_doctor = Doctor.query.get(doctor_id)
        if not selected_doctor:
            flash("Selected doctor not found.", "danger")
            return redirect(url_for('search_doctors'))
    if request.method == "POST":
        doctor_id_form = request.form.get('doctor_id', type=int)
        appointment_date_str = request.form.get('appointmentDate')
        appointment_time = request.form.get('appointmentTime')
        booking_for_other = request.form.get('bookingForOther')
        if booking_for_other:
            patient_name = request.form.get('patientName')
            symptoms = f"Patient: {patient_name}, Age: {request.form.get('patientAge')}, Phone: {request.form.get('patientPhone')}, Notes: {request.form.get('patientNotes')}"
        else:
            symptoms = request.form.get('notes')
        if not doctor_id_form or not appointment_date_str or not appointment_time or not symptoms:
            flash("Please fill in all required fields for the appointment.", "danger")
            return redirect(request.url)
        try:
            appointment_date = datetime.datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please use %Y-%m-%d.", "danger")
            return redirect(request.url)
        doctor_for_booking = Doctor.query.get(doctor_id_form)
        if not doctor_for_booking:
            flash("The selected doctor is not valid.", "danger")
            return redirect(request.url)
        new_appointment = Appointment(
            user_id=user_id,
            doctor_id=doctor_for_booking.id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            symptoms=symptoms,
            status='pending'
        )
        try:
            db.session.add(new_appointment)
            db.session.commit()
            flash("Appointment booked successfully! It is pending doctor's approval.", "success")
            return redirect(url_for('my_appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while booking the appointment: {e}", "danger")
            app.logger.error(f"Appointment booking error: {e}")
    return render_template(
        "user/book_appointment.html",
        doctor=selected_doctor,
        user=current_user
    )

@app.route("/user/my_appointments")
def my_appointments():
    if session.get("user_type") != "general":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))
    user_id = session.get("user_id")
    appointments = Appointment.query.filter_by(user_id=user_id).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    return render_template("user/my_appointments.html", appointments=appointments)

@app.route("/user/profile", methods=["GET", "POST"])
def user_profile():
    if session.get("user_type") != "general":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))
    user_id = session.get("user_id")
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        user.fullName = request.form["fullName"]
        user.email = request.form["email"]
        user.age = request.form["age"]
        user.phone = request.form["phone"]
        user.address = request.form["address"]
        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("user_profile"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", "danger")
    return render_template("user/user_profile.html", user=user)
