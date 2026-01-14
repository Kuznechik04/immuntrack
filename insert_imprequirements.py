from models import Impfrequirements
from extensions import db
from flask import Flask
from app import app  # ✅ korrekt, weil app.py im Root liegt

def main():
    print(">>> Skript gestartet <<<")

    with app.app_context():
        land = input("Land: ")
        impfstoff = input("Impfstoff: ")
        gueltigkeit_input = input("Gültigkeit in Monaten (leer lassen, wenn unbekannt): ")

        gueltigkeitsdauer = int(gueltigkeit_input) if gueltigkeit_input else None

        neue_voraussetzung = Impfrequirements(
            land=land,
            impfstoff=impfstoff,
            gueltigkeitsdauer=gueltigkeitsdauer
        )

        try:
            db.session.add(neue_voraussetzung)
            db.session.commit()
            print("✅ Impfvoraussetzung erfolgreich gespeichert!")
        except Exception as e:
            print("❌ Fehler beim Speichern:", e)

if __name__ == "__main__":
    main()
