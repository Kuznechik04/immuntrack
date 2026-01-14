from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User
from extensions import db
from flask_login import login_user, login_required, current_user, logout_user
import pyotp
import qrcode
import io
import base64

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    print("Register route accessed")
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        print(first_name, last_name, email, password, confirm_password)
        # Validierung der Eingaben



        # Passwort bestätigen
        if password != confirm_password:
            flash('Passwörter stimmen nicht überein.', 'error')
            return redirect(url_for('auth_bp.register'))

        # Benutzer prüfen
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('E-Mail ist bereits registriert.', 'error')
            return redirect(url_for('auth_bp.register'))

        # Benutzer anlegen
        new_user = User(first_name=first_name,last_name=last_name,email=email)
        new_user.set_password(password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('main_bp.registration_success'))
        except Exception as e:
            import traceback
            print("DB ERROR:", traceback.format_exc())
            flash("Fehler beim Speichern. Bitte versuche es erneut.", "error")
       # login_user(new_user)  # Direkt einloggen
        #flash('Willkommen bei ImmunTrack!', 'success')
        #return redirect(url_for('main_bp.dashboard'))

    return render_template('auth/registration.html')


# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print("Login-POST empfangen")
        print("E-Mail:", email)
        print("Passwort:", password)

        user = User.query.filter_by(email=email).first()
        print("User aus der Datenbank:", user)
        if user and user.check_password(password):
            if user.mfa_enabled:
                print("User has MFA enabled, redirecting to challenge")
                session['preauth_user_id'] = user.id
                print("Passwort korrekt, Weiterleitung zur MFA-Verifizierung")
                return redirect(url_for("auth_bp.mfa_challenge"))
            else:
                login_user(user)
                flash("Erfolgreich eingeloggt!", "success")
                print("Login erfolgreich, Weiterleitung zum Dashboard")
                return redirect(url_for('main_bp.dashboard'))
        else:
            flash("Ungültige Anmeldedaten.", "error")
            print("Login fehlgeschlagen")
            return redirect(url_for('auth_bp.login'))

    return render_template('auth/login.html')


@auth_bp.route("/login/mfa_challenge", methods=["GET", "POST"])
def mfa_challenge():
    user_id = session.get("preauth_user_id")
    if not user_id:
        return redirect(url_for("auth_bp.login"))
    user = User.query.get(user_id)
    print("Rendering MFA challenge for user:", user.email)
    if not user or not user.mfa_enabled or not user.mfa_secret:
        session.pop("preauth_user_id", None)
        return redirect(url_for("auth_bp.login"))
    if request.method == "POST":
        code = (request.form.get("code") or "").strip().replace(" ", "")
        print("POST received, code entered:", repr(code))
        totp = pyotp.TOTP(user.mfa_secret)
        print("User mfa_secret:", user.mfa_secret)
        if totp.verify(code, valid_window=1):
            print("Code verified successfully")
            session.pop("preauth_user_id", None)
            login_user(user)
            print("Redirecting to dashboard")
            flash("Erfolgreich eingeloggt!", "success")
            return redirect(url_for("main_bp.dashboard"))
        else:
            print("Code invalid")
            flash("MFA-Code ungültig.", "error")
    return render_template("mfa_challenge.html")

@auth_bp.route("/mfa/setup", methods=["GET", "POST"])
@login_required
def mfa_setup():
    if current_user.mfa_enabled:
        flash("MFA ist bereits aktiviert.", "info")
        return redirect(url_for("main_bp.dashboard"))
    if not current_user.mfa_secret:
        current_user.mfa_secret = pyotp.random_base32()
        db.session.commit()
    totp = pyotp.TOTP(current_user.mfa_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="ImmunTrack"
    )
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return render_template("mfa_setup.html", qr_b64=qr_b64)

@auth_bp.route("/mfa/verify-setup", methods=["POST"])
@login_required
def mfa_verify_setup():
    code = (request.form.get("code") or "").strip().replace(" ", "")
    if not current_user.mfa_secret:
        flash("MFA-Setup nicht initialisiert.", "error")
        return redirect(url_for("auth_bp.mfa_setup"))
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(code, valid_window=1):
        flash("Code ungültig. Bitte erneut versuchen.", "error")
        return redirect(url_for("auth_bp.mfa_setup"))
    current_user.mfa_enabled = True
    db.session.commit()
    flash("MFA erfolgreich eingerichtet.", "success")
    return redirect(url_for("main_bp.dashboard"))