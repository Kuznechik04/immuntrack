import requests
from bs4 import BeautifulSoup
from app import app, db
from models import Impfung  # Passe ggf. den Modellnamen an

URL = "https://www.rki.de/DE/A-Z/impfungen-a-z-node.html"
response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")

impfungen = set()
for link in soup.select("ul.azliste li a"):
    name = link.get_text(strip=True)
    impfungen.add(name)

with app.app_context():
    for name in impfungen:
        if not Impfung.query.filter_by(name=name).first():
            db.session.add(Impfung(name=name))
    db.session.commit()
print("Fertig!")