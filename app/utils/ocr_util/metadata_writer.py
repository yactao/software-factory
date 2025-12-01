import csv
import os
from config import METADATA_FILE
import csv
import os
from config import METADATA_FILE


def init_metadata_file(metadata_file):
    """Crée le dossier parent et le fichier CSV avec en-têtes si nécessaire."""
    metadata_dir = os.path.dirname(metadata_file)
    if metadata_dir and not os.path.exists(metadata_dir):
        os.makedirs(metadata_dir, exist_ok=True)

    if not os.path.exists(metadata_file):
        with open(metadata_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Client", "Ville", "Code Magasin",
                "Type de matériel", "N° Série", "Marque",
                "Type de gaz", "Charge de gaz", "Pression haute (HP)",
                "Pression basse (LP)", "Modèle", "Date Fab",
                "Statut OCR", "Fichier"
            ])

def append_metadata(fields, client, ville, code_magasin, statut_ocr, filename, metadata_file):
    """Ajoute une ligne au fichier CSV indiqué par metadata_file."""
    with open(metadata_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            client,
            ville,
            code_magasin,
            fields.get("Type de matériel", ""),
            fields.get("Numéro de série", ""),
            fields.get("Marque", ""),
            fields.get("Type de gaz", ""),
            fields.get("Charge de gaz", ""),
            fields.get("Pression haute (HP)", ""),
            fields.get("Pression basse (LP)", ""),
            fields.get("Modèle", ""),
            fields.get("Date de fabrication", ""),
            statut_ocr,
            filename
        ])
