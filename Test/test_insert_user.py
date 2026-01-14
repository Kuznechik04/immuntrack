import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import User
from extensions import db
from app import app

# Beispiel-Daten
first_name = "Max"
last_name = "Mustermann"
username = "testuser"
email = "testuser@example.com"
password = "geheim123"

with app.app_context():
    # Prüfen, ob der Benutzer schon existiert
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print("Benutzer existiert bereits:")
        print(f"ID: {existing_user.id}")
        print(f"Vorname: {existing_user.first_name}")
        print(f"Nachname: {existing_user.last_name}")
        print(f"Username: {existing_user.username}")
        print(f"Email: {existing_user.email}")
        print(f"Password Hash: {existing_user.password_hash}")
    else:
        # Benutzer anlegen
        user = User(first_name=first_name, last_name=last_name, username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Benutzer erfolgreich eingefügt: {user.username}, {user.email}")
        print("Alle Werte für testuser:")
        print(f"ID: {user.id}")
        print(f"Vorname: {user.first_name}")
        print(f"Nachname: {user.last_name}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Password Hash: {user.password_hash}")

    # Alle User ausgeben
    print("\nAlle User in der Datenbank:")
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}, Vorname: {user.first_name}, Nachname: {user.last_name}, Username: {user.username}, Email: {user.email}")
