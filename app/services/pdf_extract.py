# app/services/pdf_extract.py
"""Extraction de texte depuis un PDF (fallback quand l'API ne gère pas l'upload de fichier)."""

from pathlib import Path
from typing import Union

from fastapi import HTTPException


def extract_text_from_pdf(pdf_path: Union[str, Path]) -> str:
    """
    Extrait le texte d'un fichier PDF.
    Utilise pypdf. Lève HTTPException si le module est absent ou en cas d'erreur.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise HTTPException(500, f"Fichier PDF introuvable: {pdf_path}")
    try:
        from pypdf import PdfReader
    except ImportError:
        raise HTTPException(
            500,
            "Extraction PDF requiert: pip install pypdf",
        )
    try:
        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n\n".join(parts).strip() if parts else ""
    except Exception as e:
        raise HTTPException(500, f"Erreur extraction PDF: {e}")
