from flask import render_template, redirect, request, session, flash, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Doctor, Appointment
from .database import db
from flask import current_app as app
from datetime import date
from sqlalchemy.orm import joinedload
import re
from datetime import datetime

@app.route("/")
def landing_page():
    if "user_id" in session:
        user_type = session.get("user_type")
        if user_type == "admin":
            return redirect(url_for("admin_dashboard"))
        elif user_type == "doctor":
            return redirect(url_for("doctor_dashboard", user_id=session["user_id"]))
        else:
            return redirect(url_for("user_dashboard", user_id=session["user_id"]))
    return render_template("landing.html")

@app.route("/privacy-policy")
def privacy_policy():
    return render_template("content/policy.html")

@app.route("/terms")
def terms():
    return render_template("content/terms.html")

@app.route("/refund-policy")
def refund_policy():
    return render_template("content/refund.html")

@app.route("/careers")
def careers():
    return render_template("content/career.html")

@app.route("/faqs")
def faqs():
    return render_template("content/faqs.html")

@app.route("/download-app")
def download_apk():
    return render_template("content/download_apk.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            fullName = request.form.get("fullName", "").strip()
            email = request.form.get("email", "").strip()
            age = request.form.get("age", "").strip()
            phone = request.form.get("phone", "").strip()
            address = request.form.get("address", "").strip()
            plain_password = request.form.get("password", "")

            form_data = {
                "fullName": fullName,
                "email": email,
                "age": age,
                "phone": phone,
                "address": address
            }

            if not all([fullName, email, age, phone, address, plain_password]):
                flash("All fields are required.", "danger")
                return render_template("register.html", **form_data)

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash("Invalid email format.", "danger")
                return render_template("register.html", **form_data)

            if not age.isdigit() or not (0 < int(age) < 120):
                flash("Please enter a valid age.", "danger")
                return render_template("register.html", **form_data)

            if not re.match(r"^\+?\d{7,15}$", phone):
                flash("Please enter a valid phone number (min 7 digits, optional +).", "danger")
                return render_template("register.html", **form_data)

            if len(plain_password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return render_template("register.html", **form_data)

            if User.query.filter_by(email=email).first():
                flash("That email is already registered. Please log in instead.", "danger")
                return render_template("register.html", **form_data)

            hashed_password = generate_password_hash(plain_password)
            new_user = User(
                fullName=fullName,
                email=email,
                age=age,
                phone=phone,
                address=address,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration Error: {e}")
            flash("An error occurred during registration. Please try again.", "danger")
            return render_template("register.html", **request.form.to_dict())

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        user_type = session.get("user_type")
        if user_type == "admin":
            return redirect(url_for("admin_dashboard"))
        elif user_type == "doctor":
            return redirect(url_for("doctor_dashboard", user_id=session["user_id"]))
        else:
            return redirect(url_for("user_dashboard", user_id=session["user_id"]))

    if request.method == "POST":
        try:
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session["user_id"] = user.id
                session["user_type"] = user.type
                session["user_name"] = user.fullName
                session.permanent = True
                if user.type == "admin":
                    return redirect(url_for("admin_dashboard"))
                return redirect(url_for("user_dashboard", user_id=user.id))

            doctor = Doctor.query.filter_by(email=email).first()
            if doctor and check_password_hash(doctor.password, password):
                if doctor.status != "approved":
                    flash("Doctor account not approved yet.", "warning")
                    return redirect(url_for("login"))
                session["user_id"] = doctor.id
                session["user_type"] = "doctor"
                session["user_name"] = doctor.full_name
                session.permanent = True
                return redirect(url_for("doctor_dashboard", user_id=doctor.id))

            flash("Invalid email or password", "danger")

        except Exception as e:
            current_app.logger.error(f"Login Error: {e}")
            flash("An error occurred during login. Please try again.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    try:
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))
    except Exception as e:
        current_app.logger.error(f"Logout Error: {e}")
        flash("An error occurred during logout. Please try again.", "danger")
        return redirect(url_for("login"))

@app.route("/doctor_dashboard/<int:user_id>")
def doctor_dashboard(user_id):
    doctor = Doctor.query.get_or_404(user_id)
    # Ensure the user ID in the URL matches the session ID for the logged-in doctor
    if session.get("user_type") != "doctor" or session.get("user_id") != doctor.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    # FIX: Fetch appointments for this doctor, ordered by the earliest upcoming date and time
    # This will put appointments happening soonest (closest to the current date/time) at the top.
    doctor_appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(
        Appointment.appointment_date.asc(),  # Sort by date in ASCENDING order (earliest date first)
        Appointment.appointment_time.asc()   # Then by time in ASCENDING order (earliest time first on the same date)
    ).all()

    return render_template("doctor/doctor_dashboard.html", doctor=doctor, appointments=doctor_appointments)
@app.route("/toggle_clinic_status/<int:user_id>", methods=["POST"])
def toggle_clinic_status(user_id):
    doctor = Doctor.query.get_or_404(user_id)
    if session.get("user_type") != "doctor" or session.get("user_id") != doctor.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    # Toggle logic
    doctor.clinic_status = "closed" if doctor.clinic_status == "open" else "open"
    db.session.commit()
    return redirect(url_for("doctor_dashboard", user_id=doctor.id))

@app.route("/doctor/appointments/<int:user_id>")
def doctor_appointments(user_id):
    doctor = Doctor.query.get_or_404(user_id)
    if session.get("user_type") != "doctor" or session.get("user_id") != doctor.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    return render_template("doctor/doctor_appointments.html", appointments=appointments)


@app.route("/doctor/appointments/confirm/<int:appointment_id>", methods=["POST"])
def confirm_appointment_by_doctor(appointment_id):
    if session.get("user_type") != "doctor":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointment = Appointment.query.get_or_404(appointment_id)
    doctor_id = session.get("user_id")

    if appointment.doctor_id != doctor_id:
        flash("You can only confirm appointments assigned to you.", "danger")
        return redirect(url_for("doctor_appointments", user_id=doctor_id))

    token_number = request.form.get('token_number')
    if not token_number:
        flash("Token number is required to confirm an appointment.", "warning")
        return redirect(url_for("doctor_appointments", user_id=doctor_id))

    # DEBUG LOG
    print(f"[DEBUG] Doctor {doctor_id} is confirming appointment {appointment_id}")

    if appointment.status == 'pending':
        appointment.status = "confirmed"
        appointment.token_number = token_number

        try:
            db.session.commit()
            flash(f"Appointment {appointment_id} confirmed with Token: {token_number}.", "success")
            print(f"[DEBUG] Appointment {appointment_id} confirmed in DB")

            # ✅ Send push notification if fcm_token exists
            fcm_token = appointment.patient.fcm_token
            if fcm_token:
                print(f"[DEBUG] Sending push to fcm_token: {fcm_token}")
                send_push_notification(
                    player_id=fcm_token,
                    heading="Appointment Confirmed",
                    content=f"Your appointment with Dr. {appointment.doctor.full_name} is confirmed. Token: {token_number}."
                )
            else:
                print(f"[DEBUG] ❌ No fcm_token found for user {appointment.patient.id}")
                app.logger.warning(f"No fcm_token for user {appointment.patient.id}")

        except Exception as e:
            db.session.rollback()
            flash(f"Error confirming appointment: {e}", "danger")
            app.logger.error(f"[ERROR] Failed to confirm appointment {appointment_id}: {e}")
    else:
        flash(f"Appointment {appointment_id} is already '{appointment.status}'.", "warning")
        print(f"[DEBUG] Appointment {appointment_id} already {appointment.status}")

    return redirect(url_for("doctor_appointments", user_id=doctor_id))


@app.route("/doctor/appointments/cancel/<int:appointment_id>")
def cancel_appointment_by_doctor(appointment_id):
    if session.get("user_type") != "doctor":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor_id != session.get("user_id"):
        flash("You can only cancel appointments assigned to you.", "danger")
        return redirect(url_for("doctor_appointments", user_id=session.get("user_id")))

    if appointment.status in ['pending', 'confirmed']:
        appointment.status = "cancelled"
        try:
            db.session.commit()
            flash(f"Appointment {appointment_id} for {appointment.patient.fullName} cancelled.", "warning")

            # ✅ Notify patient
            if appointment.patient.player_id:
                send_push_notification(
                    player_id=appointment.patient.player_id,
                    heading="Appointment Cancelled",
                    content=f"Your appointment with Dr. {appointment.doctor.name} has been cancelled."
                )

        except Exception as e:
            db.session.rollback()
            flash(f"Error cancelling appointment: {e}", "danger")
    else:
        flash(f"Appointment {appointment_id} is already '{appointment.status}'. Cannot cancel.", "warning")

    return redirect(url_for("doctor_appointments", user_id=session.get("user_id")))

@app.route("/doctor/profile/<int:user_id>", methods=["GET", "POST"])
def doctor_profile(user_id):
    doctor = Doctor.query.get_or_404(user_id)

    if session.get("user_type") != "doctor" or session.get("user_id") != doctor.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    if request.method == "POST":
        doctor.full_name = request.form["full_name"]
        doctor.email = request.form["email"]
        doctor.phone = request.form["phone"]
        doctor.specialty = request.form["specialty"]
        doctor.available_from = request.form.get("available_from")
        doctor.available_to = request.form.get("available_to")
        doctor.morning_slot = request.form.get("morning_slot")
        doctor.afternoon_slot = request.form.get("afternoon_slot")
        doctor.evening_slot = request.form.get("evening_slot")

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
@app.route("/edit_doctor/<int:doctor_id>", methods=["GET", "POST"])
def edit_doctor(doctor_id):
    if session.get("user_type") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("login_page"))

    doctor = Doctor.query.get_or_404(doctor_id)

    if request.method == "POST":
        # 📝 Update doctor fields from form
        doctor.full_name = request.form["full_name"]
        doctor.email = request.form["email"]
        doctor.phone = request.form["phone"]
        doctor.specialty = request.form["specialty"]

        # Optional: Only update password if provided
        password_input = request.form.get("password")
        if password_input:
            doctor.password = generate_password_hash(password_input)

        doctor.status = request.form.get("status", doctor.status)
        doctor.available_from = request.form.get("available_from")
        doctor.available_to = request.form.get("available_to")
        doctor.address = request.form.get("address")
        doctor.morning_slot = request.form.get("morning_slot")
        doctor.afternoon_slot = request.form.get("afternoon_slot")
        doctor.evening_slot = request.form.get("evening_slot")

        try:
            db.session.commit()
            flash("Doctor details updated successfully.", "success")
            return redirect(url_for("manage_doctors"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating: {e}", "danger")

    return render_template("admin/edit_doctor.html", doctor=doctor)


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

    # Base query - fetch all approved doctors (open or closed)
    doctors_query = Doctor.query.filter_by(status='approved')

    # Get all approved doctors for distinct specialties list
    all_approved_doctors = doctors_query.all()
    specialties = sorted(set(d.specialty for d in all_approved_doctors if d.specialty))

    # Filters from user input
    specialty_filter = request.args.get("specialty")
    location_filter = request.args.get("location")
    name_filter = request.args.get("name")

    # Apply filters
    if specialty_filter and specialty_filter != "Choose...":
        doctors_query = doctors_query.filter(Doctor.specialty == specialty_filter)

    if location_filter:
        doctors_query = doctors_query.filter(Doctor.address.ilike(f"%{location_filter}%"))

    if name_filter:
        doctors_query = doctors_query.filter(Doctor.full_name.ilike(f"%{name_filter}%"))

    doctors = doctors_query.all()

    return render_template(
        "user/search_doctors.html",
        doctors=doctors,
        specialties=specialties,
        selected_specialty=specialty_filter or "",
        selected_location=location_filter or "",
        selected_name=name_filter or ""
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

    if request.method == "GET":
        if not doctor_id:
            flash("Please select a doctor to book an appointment.", "warning")
            return redirect(url_for('search_doctors'))

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
            symptoms = (
                f"Patient: {patient_name}, "
                f"Age: {request.form.get('patientAge')}, "
                f"Phone: {request.form.get('patientPhone')}, "
                f"Notes: {request.form.get('patientNotes')}"
            )
        else:
            symptoms = request.form.get('notes')

        if not doctor_id_form or not appointment_date_str or not appointment_time or not symptoms:
            flash("Please fill in all required fields for the appointment.", "danger")
            return redirect(request.url)

        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
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

            # ✅ Push notification to doctor
            if doctor_for_booking.fcm_token:
                send_push_notification(
                    doctor_for_booking.fcm_token,
                    "New Appointment",
                    f"{current_user.fullName} booked an appointment with you on {appointment_date} at {appointment_time}."
                )

            flash("Appointment booked successfully! It is pending doctor's approval.", "success")
            return redirect(url_for('my_appointments'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while booking the appointment: {e}", "danger")
            app.logger.error(f"Appointment booking error: {e}")
            selected_doctor = doctor_for_booking  # To keep page rendering intact

    return render_template(
        "user/book_appointment.html",
        doctor=selected_doctor,
        user=current_user,
        morning_slot=selected_doctor.morning_slot if selected_doctor else None,
        afternoon_slot=selected_doctor.afternoon_slot if selected_doctor else None,
        evening_slot=selected_doctor.evening_slot if selected_doctor else None
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
        user.age = request.form["age"]
        user.phone = request.form["phone"]
        user.address = request.form["address"]

        # Handle password change only if all fields are filled
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if current_password or new_password or confirm_password:
            if not (current_password and new_password and confirm_password):
                flash("All password fields are required to change password.", "warning")
                return redirect(url_for("user_profile"))
            if not check_password_hash(user.password, current_password):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("user_profile"))
            if new_password != confirm_password:
                flash("New passwords do not match.", "warning")
                return redirect(url_for("user_profile"))
            user.password = generate_password_hash(new_password)
            flash("Password updated successfully!", "success")

        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", "danger")

        return redirect(url_for("user_profile"))

    return render_template("user/user_profile.html", user=user)

@app.route('/sitemap')
def sitemap():
    # You might render an XML sitemap or a simple HTML page listing links
    return render_template('static_pages/sitemap.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('static_pages/disclaimer.html')

