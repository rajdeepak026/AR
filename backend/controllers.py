from flask import render_template, redirect, request, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Doctor, Appointment
from .database import db
from flask import current_app as app
import datetime
from datetime import date # Import date for today's date
from sqlalchemy.orm import joinedload # Make sure to import this

@app.route("/")
def index(): # Renamed from login_page to index for clarity
    # Check if user is already logged in
    if "user_id" in session:
        user_id = session["user_id"]
        user_type = session.get("user_type") # Use .get() to avoid KeyError if not set

        if user_type == "admin":
            return redirect(url_for("admin_dashboard"))
        elif user_type == "general":
            return redirect(url_for("user_dashboard", user_id=user_id))
        elif user_type == "doctor":
            # For doctors, also check if their status is approved if needed,
            # but usually, this check happens at initial login.
            # Here we just redirect if they are already in session.
            return redirect(url_for("doctor_dashboard", user_id=user_id))
    # If no user_id in session, show the login page
    return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullName = request.form["fullName"]
        email = request.form["email"]
        age = request.form["age"]
        phone = request.form["phone"]
        address = request.form["address"]
        # Get the plain password for validation before hashing
        plain_password = request.form["password"]

        # Validate password length
        if len(plain_password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return redirect(url_for("register"))

        password = generate_password_hash(plain_password)

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
            session.permanent = True # <--- Add this line for permanent user session
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
            session.permanent = True # <--- Add this line for permanent doctor session
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


# --- Updated /doctor/appointments/confirm/<int:appointment_id> route ---
@app.route("/doctor/appointments/confirm/<int:appointment_id>", methods=["POST"])
def confirm_appointment_by_doctor(appointment_id):
    """
    Doctor route to confirm a pending appointment.
    Requires a token number from the form.
    """
    if session.get("user_type") != "doctor":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointment = Appointment.query.get_or_404(appointment_id)

    # Ensure the doctor is confirming their own appointment
    if appointment.doctor_id != session.get("user_id"):
        flash("You can only confirm appointments assigned to you.", "danger")
        return redirect(url_for("doctor_appointments", user_id=session.get("user_id")))

    # Retrieve the token number from the form submission
    token_number = request.form.get('token_number')

    if not token_number:
        flash("Token number is required to confirm an appointment.", "warning")
        return redirect(url_for("doctor_appointments", user_id=session.get("user_id")))

    if appointment.status == 'pending':
        appointment.status = "confirmed"
        # Assign the token number provided by the doctor
        appointment.token_number = token_number

        try:
            db.session.commit()
            flash(f"Appointment {appointment_id} for {appointment.patient.fullName} confirmed with Token: {token_number}.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error confirming appointment: {e}", "danger")
    else:
        flash(f"Appointment {appointment_id} is already '{appointment.status}'. Only pending appointments can be confirmed.", "warning")
    
    # Redirect back to the doctor's appointments page
    return redirect(url_for("doctor_appointments", user_id=session.get("user_id")))


# --- Original /doctor/appointments/cancel/<int:appointment_id> route ---
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
        return redirect(url_for("doctor_appointments", user_id=session.get("user_id")))

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
    
    # Redirect back to the doctor's appointments page
    return redirect(url_for("doctor_appointments", user_id=session.get("user_id")))

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
    # Check if the user is an admin
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    # Get total count of users and doctors
    total_users = User.query.count()
    total_doctors = Doctor.query.count()

    # Calculate today's appointments
    today = date.today()
    todays_appointments = Appointment.query.filter_by(appointment_date=today).count()

    # Calculate total revenue: 20 rupees per appointment for ALL appointments
    # First, get the total count of all appointments
    total_appointments_count = Appointment.query.count()
    # Then, multiply by the per-appointment fee
    total_revenue = total_appointments_count * 20 # 20 rupees per appointment

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
    all_appointments = Appointment.query \
        .options(joinedload(Appointment.doctor), joinedload(Appointment.patient)) \
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()) \
        .all()

    return render_template("admin/appointments.html", appointments=all_appointments)
@app.route("/admin/appointments/approve/<int:appointment_id>", methods=["POST"])
def approve_appointment(appointment_id):
    """
    Admin route to approve a pending appointment.
    Sets status to 'confirmed' and assigns a token number.
    """
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.status == 'pending':
        token_number = request.form.get('token_number')

        if not token_number:
            flash("Token number is required to approve an appointment.", "warning")
            return redirect(url_for("appointments"))

        appointment.status = 'confirmed'
        appointment.token_number = token_number

        try:
            db.session.commit()
            flash(f"Appointment #{appointment.id} for {appointment.patient.fullName} with Dr. {appointment.doctor.full_name} has been approved with Token: {token_number}.", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Error approving appointment: {e}", "danger")
    else:
        flash(f"Appointment #{appointment.id} is already '{appointment.status}'. Only pending appointments can be approved.", "info")

    return redirect(url_for("appointments"))


@app.route("/admin/appointments/delete/<int:appointment_id>", methods=["POST"])
def delete_appointment(appointment_id):
    """
    Admin route to delete an appointment.
    """
    # 1. Authorization Check: Only admins should be able to delete appointments
    if session.get("user_type") != "admin":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login_page"))

    # 2. Retrieve the appointment
    appointment = Appointment.query.get_or_404(appointment_id)

    # 3. Perform the deletion
    try:
        db.session.delete(appointment)
        db.session.commit()
        flash(f"Appointment {appointment.id} for {appointment.patient.fullName} has been successfully deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting appointment {appointment.id}: {e}", "danger")

    # 4. Redirect back to the appointments list
    return redirect(url_for("appointments"))
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
        status = request.form.get("status", "pending") # Get status from form, default to pending

        # Get general availability times (assuming these fields exist elsewhere in your form)
        available_from_str = request.form.get("available_from")
        available_to_str = request.form.get("available_to")

        # Get the new address field
        address = request.form.get("address") # Retrieve the address from the form

        # NEW: Get specific availability slot values from the form
        morning_slot = request.form.get("morning_slot")
        afternoon_slot = request.form.get("afternoon_slot")
        evening_slot = request.form.get("evening_slot")

        new_doctor = Doctor(
            full_name=full_name,
            email=email,
            phone=phone,
            specialty=specialty,
            password=password,
            status=status,
            available_from=available_from_str,    # Store as string (HH:MM)
            available_to=available_to_str,         # Store as string (HH:MM)
            address=address,                       # Pass the new address field
            # NEW: Assign the specific slot values
            morning_slot=morning_slot,
            afternoon_slot=afternoon_slot,
            evening_slot=evening_slot
        )

        try:
            db.session.add(new_doctor)
            db.session.commit()
            flash("Doctor added successfully and is pending approval.", "success")
            return redirect(url_for("manage_doctors"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}. Email might be in use.", "danger")
            # For debugging, you might print e or log it
            # print(f"Error adding doctor: {e}")

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

    # Get all approved doctors to extract unique specialties for the dropdown
    # It's good practice to get all approved doctors first, then extract specialties
    all_approved_doctors = Doctor.query.filter_by(status='approved').all()
    specialties = sorted(list(set([d.specialty for d in all_approved_doctors if d.specialty]))) # Added check for None specialty

    specialty_filter = request.args.get("specialty")
    location_filter = request.args.get("location")

    if specialty_filter and specialty_filter != "Choose...":
        doctors_query = doctors_query.filter_by(specialty=specialty_filter)

    # Activate location filtering
    if location_filter:
        # Use ilike for case-insensitive partial match on the address field
        doctors_query = doctors_query.filter(Doctor.address.ilike(f'%{location_filter}%'))
        flash("Location search results are displayed.", "info") # Optional: update message

    # No need for the 'else' block that flashed the "not implemented" message now

    doctors = doctors_query.all()

    return render_template(
        "user/search_doctors.html",
        doctors=doctors,
        specialties=specialties,
        selected_specialty=specialty_filter if specialty_filter else "", # Changed default to empty string for 'All Specialties'
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
