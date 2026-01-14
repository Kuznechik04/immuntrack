import json
import csv
import re
import unicodedata

def normalize_name(name):
    """
    Normalisiert einen String für eine URL:
    - Entfernt Klammern und ihren Inhalt
    - Konvertiert zu Kleinbuchstaben
    - Ersetzt Umlaute (ä -> ae, etc.)
    - Ersetzt Leerzeichen und Sonderzeichen durch Bindestriche
    """
    # Entfernt Inhalte in Klammern, z.B. (Reise nach)
    name = re.sub(r'\(.*\)', '', name).strip()
    
    # Konvertiert zu Kleinbuchstaben
    name = name.lower()
    
    # Ersetzt deutsche Umlaute
    replacements = {
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'ß': 'ss'
    }
    for char, replacement in replacements.items():
        name = name.replace(char, replacement)
        
    # Normalisiert andere diakritische Zeichen (z.B. é -> e)
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    
    # Ersetzt verbleibende ungültige Zeichen durch Bindestriche
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'[\s_]+', '-', name)
    
    return name

def is_country(entry_name):
    """
    Einfacher Filter, um Nicht-Länder-Einträge auszuschließen.
    """
    name_lower = entry_name.lower()
    # Schließt explizite Weiterleitungen und Themen-Keywords aus
    exclude_keywords = [
        'siehe', 'visum', 'impfungen', 'pass', 'amt', 'reise', 
        'warnung', 'medikamente', 'app', 'arbeit', 'studium', 
        'kinder', 'apostille', ':', '(', ')', '?'
    ]
    
    if any(keyword in name_lower for keyword in exclude_keywords):
        return False
        
    # Schließt sehr kurze oder sehr lange Namen aus (willkürliche Annahme)
    if len(entry_name) < 3 or len(entry_name) > 40:
        return False
        
    return True

# --- Hauptskript ---

json_file_path = 'traveladvice.json'

output_csv_path = 'laender_links.csv'
base_url = 'https://www.auswaertiges-amt.de/de/service/laender/'

# Liste für die gefilterten Daten
data_to_write = []
# Zähler für die fortlaufende ID
current_id = 1

try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        all_entries = json.load(f)

    for entry in all_entries:
        name = entry.get('name', '')
        suffix = entry.get('value', '')
        
        # Filtern, um nur wahrscheinliche Länder zu erhalten
        if is_country(name):
            # Den 'name' als Basis für den Slug nehmen
            slug = normalize_name(name)
            
            # Den Link zur Haupt-Länderseite generieren
            generated_link = f"{base_url}{slug}-node/{suffix}"
            
            # Die fortlaufende ID, den Namen und den Link hinzufügen
            data_to_write.append([current_id, name, generated_link])
            
            # ID für den nächsten Eintrag erhöhen
            current_id += 1

    # In eine CSV-Datei schreiben
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header schreiben (angepasst)
        writer.writerow(['landid', 'bezeichnung', 'generierter_link'])
        # Daten schreiben
        writer.writerows(data_to_write)
        
    print(f"Erfolgreich! Daten wurden in '{output_csv_path}' gespeichert.")
    print(f"Insgesamt {len(data_to_write)} wahrscheinliche Länder gefunden.")

except FileNotFoundError:
    print(f"Fehler: Die Datei '{json_file_path}' wurde nicht gefunden.")
except json.JSONDecodeError:
    print(f"Fehler: Die Datei '{json_file_path}' ist keine gültige JSON-Datei.")
except Exception as e:
    print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")