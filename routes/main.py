from datetime import date, datetime, timedelta

import os
import smtplib
from email.message import EmailMessage

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from extensions import db
from models import (
    User,
    Impfpass,                 # Alias -> Vaccination
    Impfrequirements,         # Alias -> VaccinationRequirement
    Vaccination,
    VaccinationDate,
    Vaccine,
    Country,
    VaccinationRequirement
)

main_bp = Blueprint("main_bp", __name__)


# =====================================================
# Öffentliche Seiten
# =====================================================

@main_bp.route("/")
@main_bp.route("/landingpage")
def landingpage():
    return render_template("info/navigation-bar/landingpage.html")


@main_bp.route("/about")
def about():
    return render_template("info/navigation-bar/about.html")


@main_bp.route("/security")
def security():
    return render_template("info/navigation-bar/security.html")


@main_bp.route("/legal-notice")
def legal_notice():
    return render_template("info/footer/legal-notice.html")


@main_bp.route("/privacy-policy")
def privacy_policy():
    return render_template("info/footer/privacy-policy.html")


@main_bp.route("/terms-of-use")
def terms_of_use():
    return render_template("info/footer/terms-of-use.html")


@main_bp.route("/copyright")
def copyright():
    return render_template("info/footer/copyright.html")


# =====================================================
# Kontakt
# =====================================================

@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        vorname = request.form.get("vorname")
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        msg = EmailMessage()
        msg["Subject"] = "Neue Kontaktanfrage bei ImmunTrack"
        msg["From"] = os.getenv("IMT_MAIL_FROM", "mail@immuntrack.de")
        msg["To"] = os.getenv("IMT_MAIL_TO", "mail@immuntrack.de")
        msg.set_content(f"Von: {vorname} {name}\nE-Mail: {email}\n\nNachricht:\n{message}")

        # Bitte SMTP-Zugangsdaten NICHT hardcoden:
        smtp_host = os.getenv("IMT_SMTP_HOST", "smtp.ionos.de")
        smtp_port = int(os.getenv("IMT_SMTP_PORT", "587"))
        smtp_user = os.getenv("IMT_SMTP_USER")  # z.B. mail@immuntrack.de
        smtp_pass = os.getenv("IMT_SMTP_PASS")  # Passwort aus ENV

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            flash("Nachricht erfolgreich gesendet!", "success")
            return redirect(url_for("main_bp.thank_you"))

        except Exception:
            flash(
                "Fehler beim Senden der Nachricht. Bitte versuchen Sie es erneut oder wenden Sie sich direkt an support@immuntrack.de",
                "error"
            )
            return render_template("info/navigation-bar/contact/contact.html", form_error=True)

    return render_template("info/navigation-bar/contact/contact.html", form_error=None)


@main_bp.route("/thank-you")
def thank_you():
    return render_template("info/navigation-bar/contact/thank-you.html")


# =====================================================
# Auth-Seiten (nur Templates)
# =====================================================

@main_bp.route("/registration")
def registration():
    return render_template("auth/registration.html")


@main_bp.route("/registration-success")
def registration_success():
    return render_template("auth/registration-success.html")


@main_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash(
            "Wenn diese E-Mail-Adresse existiert, wurde eine E-Mail zum Zurücksetzen des Passworts gesendet.",
            "success"
        )
        return render_template("auth/forgot-password.html", success_message=True)

    return render_template("auth/forgot-password.html")


# =====================================================
# Hilfsfunktionen für Requirements-Check
# =====================================================

def _build_user_illness_profile(user_id: int) -> dict:
    """
    Aggregiert userbezogene Impf-Daten pro Krankheit (illness_id):
    - dose_count: Summe aller gespeicherten Termine (VaccinationDate)
    - last_dose_date: letztes Datum (max)
    """
    vaccinations = (
        Vaccination.query
        .filter_by(user_id=user_id)
        .options(
            joinedload(Vaccination.vaccine).joinedload(Vaccine.illness),
            joinedload(Vaccination.dates)
        )
        .all()
    )

    profile = {}
    for v in vaccinations:
        if not v.vaccine:
            continue

        illness_id = v.vaccine.illness_id
        if illness_id is None:
            continue

        entry = profile.setdefault(illness_id, {"dose_count": 0, "last_dose_date": None})

        for d in (v.dates or []):
            entry["dose_count"] += 1
            if entry["last_dose_date"] is None or d.date > entry["last_dose_date"]:
                entry["last_dose_date"] = d.date

    return profile


def _requirement_satisfied(req: VaccinationRequirement, illness_profile: dict) -> bool:
    """
    Erfüllt, wenn:
    - Dosen >= required_doses
    - und (falls validity_period_months gesetzt) letzte Dosis nicht "zu alt" ist
      (vereinfachte Monatsrechnung: 30 Tage pro Monat).
    """
    user_entry = illness_profile.get(req.illness_id)
    if not user_entry:
        return False

    if user_entry["dose_count"] < req.required_doses:
        return False

    if req.validity_period_months is not None:
        last_date = user_entry["last_dose_date"]
        if last_date is None:
            return False

        threshold = date.today() - timedelta(days=30 * int(req.validity_period_months))
        if last_date < threshold:
            return False

    return True


# =====================================================
# Dashboard (nur für eingeloggte Nutzer)
# =====================================================

@main_bp.route("/dashboard", endpoint="dashboard")
@login_required
def dashboard():
    illness_profile = _build_user_illness_profile(current_user.id)

    countries = Country.query.options(joinedload(Country.requirements)).all()
    impfstatus = {}

    # Ziel: wie vorher – pro Land "fehlende Anforderungen" (als Zahl) für die Karte/Übersicht
    for c in countries:
        missing = 0
        for req in (c.requirements or []):
            if not _requirement_satisfied(req, illness_profile):
                missing += 1

        # Country.iso_code ist 3-stellig (z.B. "DEU"). Falls eure SVG 2-stellig nutzt,
        # müsst ihr entweder die DB anpassen oder im Template mappen.
        impfstatus[c.iso_code] = missing

    return render_template("dashboard/dashboard.html", impfstatus=impfstatus)


@main_bp.route("/account-settings", methods=["GET", "POST"])
@login_required
def account_settings():
    return render_template("dashboard/account-settings.html")


# =====================================================
# Impfungen verwalten
# =====================================================

@main_bp.route("/manage-vaccine-records")
@login_required
def manage_vaccine_records():
    # Damit Templates sauber zugreifen können: impfung.vaccine.name / impfung.vaccine.manufacturer / impfung.dates
    impfungen = (
        Impfpass.query
        .filter_by(user_id=current_user.id)
        .options(
            joinedload(Vaccination.vaccine),
            joinedload(Vaccination.dates)
        )
        .all()
    )

    return render_template("dashboard/manage-vaccine-records.html", impfungen=impfungen)


@main_bp.route("/add_vaccine", methods=["GET", "POST"])
@login_required
def add_vaccine():
    vaccines = Vaccine.query.options(joinedload(Vaccine.illness)).all()

    if request.method == "POST":
        vaccine_id = request.form.get("vaccine_id")
        status = request.form.get("status")
        date_str = request.form.get("datum") or request.form.get("date") or request.form.get("vaccination_date")

        if not vaccine_id or not status:
            flash("Bitte Impfstoff und Status angeben.", "error")
            return render_template("add_vaccine.html", vaccines=vaccines)

        v = Vaccination(
            user_id=current_user.id,
            vaccine_id=int(vaccine_id),
            status=status
        )

        # Optional: ein Datum als erster Termin
        if date_str:
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                v.dates.append(VaccinationDate(date=parsed_date))
            except ValueError:
                flash("Datum muss im Format YYYY-MM-DD sein.", "error")
                return render_template("add_vaccine.html", vaccines=vaccines)

        db.session.add(v)
        db.session.commit()

        flash("Impfung erfolgreich hinzugefügt!", "success")
        return redirect(url_for("main_bp.manage_vaccine_records"))

    return render_template("add_vaccine.html", vaccines=vaccines)


@main_bp.route("/delete_impfung/<int:impfung_id>", methods=["POST"])
@login_required
def delete_impfung(impfung_id):
    impfung = Impfpass.query.get_or_404(impfung_id)

    if impfung.user_id != current_user.id:
        flash("Du darfst nur deine eigenen Einträge löschen.", "error")
        return redirect(url_for("main_bp.manage_vaccine_records"))

    db.session.delete(impfung)
    db.session.commit()
    flash("Impfung wurde gelöscht.", "success")
    return redirect(url_for("main_bp.manage_vaccine_records"))


@main_bp.route("/meine_impfungen")
@login_required
def meine_impfungen():
    impfungen = (
        Impfpass.query
        .filter_by(user_id=current_user.id)
        .options(joinedload(Vaccination.vaccine), joinedload(Vaccination.dates))
        .all()
    )
    return render_template("meine_impfungen.html", impfungen=impfungen)


# =====================================================
# Requirements-Ansicht
# =====================================================

@main_bp.route("/impfrequirements")
def impfrequirements():
    requirements = (
        Impfrequirements.query
        .options(joinedload(VaccinationRequirement.country), joinedload(VaccinationRequirement.illness))
        .all()
    )
    return render_template("impfrequirements.html", requirements=requirements)


# =====================================================
# Einreise-Karte (Prozent erfüllt statt "fehlend")
# =====================================================

@main_bp.route("/einreise_map")
@login_required
def einreise_map():
    illness_profile = _build_user_illness_profile(current_user.id)

    countries = Country.query.options(joinedload(Country.requirements)).all()
    impfstatus = {}

    for c in countries:
        reqs = c.requirements or []
        if not reqs:
            impfstatus[c.iso_code] = 100
            continue

        met = 0
        for req in reqs:
            if _requirement_satisfied(req, illness_profile):
                met += 1

        percent = round((met / len(reqs)) * 100)
        impfstatus[c.iso_code] = percent

    return render_template("dashboard/einreise_map.html", impfstatus=impfstatus)


# =====================================================
# Fehlerbehandlung
# =====================================================

@main_bp.app_errorhandler(400)
@main_bp.app_errorhandler(401)
@main_bp.app_errorhandler(403)
@main_bp.app_errorhandler(404)
@main_bp.app_errorhandler(405)
@main_bp.app_errorhandler(408)
@main_bp.app_errorhandler(429)
@main_bp.app_errorhandler(500)
@main_bp.app_errorhandler(502)
@main_bp.app_errorhandler(503)
@main_bp.app_errorhandler(504)
def handle_error(error):
    error_code = getattr(error, "code", 500)
    return render_template("error.html", error_code=error_code), error_code
