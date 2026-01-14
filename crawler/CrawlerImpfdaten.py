import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
 
# --- Konfiguration ---
INPUT_CSV = './laender_links.csv' 
OUTPUT_CSV = './laender_impf_details.csv'
BASE_URL = 'https://www.auswaertiges-amt.de'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def extract_recommendations(security_url):
    """
    NEUE LOGIK (V11):
    Sammelt den Text als ganzen Block, *bevor* er in Sätze aufgeteilt
    und analysiert wird. Behebt das Problem mit getrennten Wörtern.
    Sucht jetzt auch flexibler nach "nachweis" (statt "nachweisen").
    """
    try:
        response = requests.get(security_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return f"Fehler: Status-Code {response.status_code}", "", security_url
        
        soup_security = BeautifulSoup(response.text, 'lxml')
        
        # 1. Finde <h2>Gesundheit</h2>
        h2_gesundheit = soup_security.find('h2', string=re.compile(r'Gesundheit'))
        if not h2_gesundheit:
            h2_gesundheit = soup_security.find('h2', id='content_4')
            if not h2_gesundheit:
                 return "Abschnitt 'Gesundheit' (h2) nicht gefunden", "", security_url
        
        # 2. Finde <h3>Impfschutz</h3> direkt danach
        h3_impfschutz = h2_gesundheit.find_next('h3', string=re.compile(r'Impfschutz'))
        if not h3_impfschutz:
            return "Abschnitt 'Impfschutz' (h3) nicht gefunden", "", security_url

        # 3. Sammle alle Textblöcke (aus <p>, <ul> und <div>) bis zum nächsten <h3>
        text_blocks = []
        for sibling in h3_impfschutz.next_siblings:
            # Stoppe bei der nächsten Überschrift
            if sibling.name == 'h3' or sibling.name == 'h2':
                break
            
            # Sammle Text aus allen relevanten Tags
            if sibling.name in ['p', 'ul', 'ol', 'div']:
                # separator=' ' sorgt dafür, dass Wörter aus Links/Listen
                # mit Leerzeichen verbunden werden, nicht aneinander kleben.
                raw_text = sibling.get_text(separator=' ', strip=True)
                text_blocks.append(raw_text)

        if not text_blocks:
            return "Kein Text unter 'Impfschutz' gefunden.", "", security_url

        # 4. Kombiniere alle Blöcke zu einem einzigen Text
        full_text = " ".join(text_blocks)
        
        # 5. Spalte den Text in Sätze auf (an Punkten oder Listenpunkten '•')
        # Wir fügen die Trennzeichen temporär hinzu, um sie nicht zu verlieren
        full_text = re.sub(r'([.•])', r'\1##SPLIT##', full_text)
        sentences = full_text.split('##SPLIT##')

        # 6. Analysiere die Sätze
        voraussetzungen_saetze = []
        empfehlungen_saetze = []

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue
                
            sentence_lower = sentence_clean.lower()
            
            # --- KORRIGIERTE LOGIK ---
            # Logik 1: Voraussetzungen (sucht jetzt nach "nachweis")
            if "müssen" in sentence_lower or "nachweis" in sentence_lower:
                voraussetzungen_saetze.append(sentence_clean)
                
            # Logik 2: Empfehlungen
            if sentence_lower.startswith("als reiseimpfungen werden impfungen gegen") and "empfohlen" in sentence_lower:
                empfehlungen_saetze.append(sentence_clean)

        # 7. Formatiere den Output-Text
        voraussetzungen_str = " ".join(voraussetzungen_saetze) if voraussetzungen_saetze else "Keine Angaben"
        empfehlungen_str = " ".join(empfehlungen_saetze) if empfehlungen_saetze else "Keine Angaben"

        return voraussetzungen_str, empfehlungen_str, security_url
        
    except requests.exceptions.RequestException as e:
        return f"Netzwerkfehler: {e}", "", security_url
    except Exception as e:
        return f"Allgemeiner Parsing-Fehler: {e}", "", security_url

# --- Hauptskript ---
results = []

try:
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        countries = list(reader)
        
    total_countries = len(countries)

    for i, row in enumerate(countries):
        # Begrenzung auf 5 Einträge, wie gewünscht
        if i >= 5:
            break 
            
        landid = row['landid']
        bezeichnung = row['bezeichnung']
        overview_url = row['generierter_link']
        
        voraussetzungen = ""
        empfehlungen = ""
        security_url = "" 
        
        try:
            # URL-Logik (V7)
            last_slash_index = overview_url.rfind('/')
            page_id = overview_url[last_slash_index+1:]
            base_node_url = overview_url[:last_slash_index] 
            slug = base_node_url.split('/')[-1].replace('-node', '')
            security_url = f"{base_node_url}/{slug}sicherheit/{page_id}"
            
            # Funktionsaufruf erwartet jetzt zwei Info-Strings
            voraussetzungen, empfehlungen, final_url = extract_recommendations(security_url)
            
        except Exception as e:
            voraussetzungen = f"Fehler beim Erstellen der URL: {e}"
            empfehlungen = "" # Zweites Feld bleibt leer
            final_url = overview_url
        
        # Füge die neuen Spalten zum Ergebnis hinzu
        results.append([landid, bezeichnung, voraussetzungen, empfehlungen, final_url])
        
        time.sleep(0.5)

    # Schreibe alle Ergebnisse in die neue CSV-Datei
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header-Spalten angepasst
        writer.writerow(['landid', 'bezeichnung', 'impf_voraussetzungen', 'impf_empfehlungen', 'quelle_url'])
        writer.writerows(results)
        
except FileNotFoundError:
    pass # Keine Ausgabe
except Exception as e:
    pass # Keine Ausgabe