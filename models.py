from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# =====================
# User
# =====================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=False)
    mfa_secret = db.Column(db.Text, nullable=True)

    vaccinations = db.relationship(
        "Vaccination",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =====================
# Illness (Krankheit)
# =====================
class Illness(db.Model):
    __tablename__ = 'illnesses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    vaccines = db.relationship(
        "Vaccine",
        back_populates="illness"
    )

    requirements = db.relationship(
        "VaccinationRequirement",
        back_populates="illness"
    )


# =====================
# Vaccine (Impfstoff)
# =====================
class Vaccine(db.Model):
    __tablename__ = 'vaccines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)

    illness_id = db.Column(db.Integer, db.ForeignKey('illnesses.id'), nullable=False)
    illness = db.relationship("Illness", back_populates="vaccines")


# =====================
# Vaccination (Impfung eines Users)
# =====================
class Vaccination(db.Model):
    __tablename__ = 'vaccinations'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", back_populates="vaccinations")

    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id'), nullable=False)
    vaccine = db.relationship("Vaccine")

    dates = db.relationship(
        "VaccinationDate",
        back_populates="vaccination",
        cascade="all, delete-orphan"
    )


# =====================
# VaccinationDate (mehrere Termine pro Impfung)
# =====================
class VaccinationDate(db.Model):
    __tablename__ = 'vaccination_dates'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)

    vaccination_id = db.Column(
        db.Integer,
        db.ForeignKey('vaccinations.id'),
        nullable=False
    )

    vaccination = db.relationship("Vaccination", back_populates="dates")


# =====================
# Country
# =====================
class Country(db.Model):
    __tablename__ = 'countries'

    id = db.Column(db.Integer, primary_key=True)
    iso_code = db.Column(db.String(3), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

    requirements = db.relationship(
        "VaccinationRequirement",
        back_populates="country"
    )


# =====================
# VaccinationRequirement
# =====================
class VaccinationRequirement(db.Model):
    __tablename__ = 'vaccination_requirements'

    id = db.Column(db.Integer, primary_key=True)

    country_id = db.Column(
        db.Integer,
        db.ForeignKey('countries.id'),
        nullable=False
    )
    illness_id = db.Column(
        db.Integer,
        db.ForeignKey('illnesses.id'),
        nullable=False
    )

    validity_period_months = db.Column(db.Integer, nullable=True)
    required_doses = db.Column(db.Integer, nullable=False)
    crawl_last_set = db.Column(db.DateTime, default=datetime.utcnow)

    country = db.relationship("Country", back_populates="requirements")
    illness = db.relationship("Illness", back_populates="requirements")


# Backwards-compatibility aliases for older German names used elsewhere in the codebase
# `Impfpass` mapped to `Vaccination` and `Impfrequirements` mapped to `VaccinationRequirement`
Impfpass = Vaccination
Impfrequirements = VaccinationRequirement
