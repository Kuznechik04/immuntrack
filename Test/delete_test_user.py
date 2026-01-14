import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import User
from extensions import db
from app import app

with app.app_context():
    user_to_delete = User.query.filter_by(email="testuser@example.com").first()
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
        print("Testuser wurde gelöscht.")
    else:
        print("Testuser nicht gefunden, nichts gelöscht.")