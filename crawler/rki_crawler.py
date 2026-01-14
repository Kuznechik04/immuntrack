import csv
import requests
from bs4 import BeautifulSoup
import urllib3

# Unsichere Verbindungen zulassen (Selbstverantwortung!)
urllib3.disable_warnings()

def crawl_rki_vaccines():
    """
    Crawlt die RKI-Webseite, extrahiert Impfstoffnamen und speichert sie in einer CSV.
    """
    
    URL = "https://www.rki.de/DE/A-Z/impfungen-a-z-node.html"
    CSV_FILE = "impfstoffe.csv"
    
    print(f"Rufe Webseite auf: {URL}")
    
    try:
        # 1. Webseite herunterladen
        # response = requests.get(URL, verify=False)  # Nur verwenden, wenn Sie der Quelle vertrauen!
        response = requests.get(URL)
        
        # Nach dem requests.get():
        print(f"Status Code: {response.status_code}")
        print("HTML Inhalt der ersten 500 Zeichen:")
        print(response.text[:500])
        
        # Fehler werfen, falls die Seite nicht erfolgreich geladen wurde (z.B. 404, 500)
        response.raise_for_status() 
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Webseite: {e}")
        return

    # 2. HTML-Inhalt analysieren (parsen)
    # Wir verwenden BeautifulSoup, um die HTML-Struktur zu durchsuchen
    soup = BeautifulSoup(response.content, 'html.parser')

    # Suche nach dem Tiles-Container
    tiles_container = soup.find('div', class_='c-tiles')
    if not tiles_container:
        print("Konnte den 'c-tiles' Bereich nicht finden. Möglicherweise hat sich die Seitenstruktur geändert.")
        return

    # Suche nach der Tiles-Liste
    tiles_list = tiles_container.find('ul', class_='c-tiles__list')
    if not tiles_list:
        print("Konnte die 'c-tiles__list' nicht finden. Möglicherweise hat sich die Seitenstruktur geändert.")
        return

    vaccine_data = []
    seen_names = set()
    vaccine_id_counter = 1

    # Finde alle Listenelemente mit der Klasse c-tiles__item
    list_items = tiles_list.find_all('li', class_='c-tiles__item')
    
    for item in list_items:
        # Den Link im Listeneintrag finden
        link = item.find('a')
        
        if link and link.text:
            vaccine_name = link.text.strip()
            if vaccine_name and vaccine_name not in seen_names:
                vaccine_data.append([vaccine_id_counter, vaccine_name])
                seen_names.add(vaccine_name)
                vaccine_id_counter += 1

    if not vaccine_data:
        print("Keine Impfstoffdaten gefunden. Möglicherweise hat sich die Seitenstruktur geändert.")
        return

    # 7. Daten in eine CSV-Datei schreiben
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            # Erstelle einen CSV-Writer
            writer = csv.writer(f)
            
            # Schreibe die Kopfzeile
            writer.writerow(['impfstoff_id', 'name'])
            
            # Schreibe alle gefundenen Daten
            writer.writerows(vaccine_data)
            
        print(f"Erfolg! {len(vaccine_data)} Impfstoffe wurden in '{CSV_FILE}' gespeichert.")
        
    except IOError as e:
        print(f"Fehler beim Schreiben der CSV-Datei: {e}")

# --- Das Skript ausführen ---
if __name__ == "__main__":
    crawl_rki_vaccines()