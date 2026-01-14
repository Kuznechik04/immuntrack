import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text('SELECT 1'))
        print("Datenbankverbindung erfolgreich!")
    except Exception as e:
        print("Fehler bei der Datenbankverbindung:", str(e))