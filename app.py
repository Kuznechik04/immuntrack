# app.py
from flask import Flask
from extensions import db, migrate  # Jetzt aus extensions importieren
from routes.auth import auth_bp
from routes.main import main_bp
from flask_login import LoginManager
from models import User

app = Flask(__name__, template_folder='templates')  # Stelle sicher, dass 'templates' der richtige Ordner ist
app.secret_key = 'ein_geheimer_schlüssel_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:neues_passwort@localhost/immuntrack'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate.init_app(app, db)

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'users'
            ) THEN
                ALTER TABLE users
                ALTER COLUMN password_hash TYPE TEXT;
            END IF;
        END
        $$;
        """))
        conn.commit()
# Update database schema
#with app.app_context():
 #   with db.engine.connect() as conn:
  #      conn.execute(db.text("ALTER TABLE users ALTER COLUMN password_hash TYPE TEXT;"))
   #     conn.commit()

# Blueprints registrieren
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.init_app(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)