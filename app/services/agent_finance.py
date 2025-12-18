# app/services/agent_finance.py

import json
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.core.config import KIMI_MODEL_SINGLE
from app.services.kimi_client import get_kimi_client
from app.services.blob_finance_excel import download_finance_excel_to_temp


def _normalize_chart_axes(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    S'assure que pour les graphiques bar ou line horizontaux ou verticaux on a
      x comme catégorie texte par exemple nom du magasin
      y comme valeur numérique int ou float

    Si le modèle a inversé par exemple x égal nombre et y égal nom de magasin
    on inverse x et y pour chaque point de la série.
    """

    if not chart:
        return chart

    ctype = chart.get("type")
    if ctype not in ("bar", "horizontal_bar", "line", "bubble"):
        return chart

    series = chart.get("series") or []
    for serie in series:
        points = serie.get("points") or []
        if not points:
            continue

        num_x = sum(isinstance(p.get("x"), (int, float)) for p in points)
        str_y = sum(isinstance(p.get("y"), str) for p in points)

        if num_x >= len(points) / 2 and str_y >= len(points) / 2:
            for p in points:
                p["x"], p["y"] = p.get("y"), p.get("x")

    return chart

def answer_finance_with_kimi(
    question: str,
    history_pairs: List[Dict[str, str]],
) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Analyse le fichier Excel finance avec Kimi.

    FIX:
      - Le LLM renvoie directement les lignes utilisées (rows) en entier.
      - Plus de row_indices, plus de fallback [0..4].
      - On valide côté backend que chaque row renvoyée existe bien dans les données envoyées au LLM.
        (anti-hallucination)
    """

    q = (question or "").strip()
    if not q:
        raise HTTPException(400, "Question vide.")

    # 1 Télécharger l'Excel depuis Azure Blob
    try:
        xlsx_path = download_finance_excel_to_temp()
    except Exception as e:
        raise HTTPException(
            500,
            f"Erreur lors du chargement du fichier Excel finance: {e}",
        )

    # 2 Charger l'Excel côté backend avec pandas
    try:
        df = pd.read_excel(xlsx_path)
        df = df.dropna(how="all").reset_index(drop=True)
    except Exception as e:
        raise HTTPException(500, f"Erreur lecture Excel finance: {e}")

    if df.empty:
        raise HTTPException(500, "Le fichier Excel finance est vide.")

    # On limite le nombre de lignes envoyées au LLM
    MAX_ROWS_FOR_LLM = 300
    df_llm = df.head(MAX_ROWS_FOR_LLM).copy()

    # Conversion en JSON liste de lignes
    records = df_llm.to_dict(orient="records")
    data_json = json.dumps(records, ensure_ascii=False)

    # Liste des colonnes avec type
    columns_info: List[Dict[str, Any]] = []
    for col in df_llm.columns:
        col_type = str(df_llm[col].dtype)
        columns_info.append({"name": col, "dtype": col_type})
    columns_json = json.dumps(columns_info, ensure_ascii=False)

    # 3 Historique compact
    hist_lines: List[str] = []
    for pair in history_pairs[-3:]:
        u = (pair.get("user") or "").strip()
        a = (pair.get("assistant") or "").strip()
        if u:
            hist_lines.append(f"U: {u}")
        if a:
            hist_lines.append(f"A: {a}")
    history_text = "\n".join(hist_lines) if hist_lines else "aucun historique pertinent."

    # Helper: serialization stable (anti-hallucination)
    def _serialize_value(v: Any) -> Any:
        if isinstance(v, (pd.Timestamp, datetime, date)):
            return v.isoformat()

        # NaN
        try:
            if isinstance(v, float) and pd.isna(v):
                return None
            if pd.isna(v):
                return None
        except TypeError:
            pass

        # NumPy scalar
        if isinstance(v, (np.generic,)):
            return v.item()

        return v

    def _canonical_row(d: Dict[str, Any]) -> str:
        """
        Canonicalisation stricte d'une row:
          - mêmes clés (toutes colonnes df_llm)
          - valeurs sérialisées JSON (dates -> iso, NaN -> None)
          - tri des clés pour stabilité
        """
        normalized: Dict[str, Any] = {}
        for c in df_llm.columns:
            normalized[c] = _serialize_value(d.get(c))
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    # Index de validation: row_canon -> row_normalized
    llm_rows_map: Dict[str, Dict[str, Any]] = {}
    for r in records:
        canon = _canonical_row(r)
        if canon not in llm_rows_map:
            # stocker la version normalisée complète
            full_norm = {c: _serialize_value(r.get(c)) for c in df_llm.columns}
            llm_rows_map[canon] = full_norm

    # 4 Prompt système orienté data et finance (MODIFIÉ: rows complets)
    system_content = (
        "Tu es un expert data analyst et finance pour un client de la grande distribution.\n"
        "Tu disposes d'une table de magasins issue d'un fichier Excel.\n\n"
        "Règles importantes\n"
        "  1 Tu réponds strictement à partir des données de la table fournie.\n"
        "  2 Si une information n'est pas présente ou pas déductible tu le dis clairement.\n"
        "  3 Tu peux faire des calculs simples comme somme moyenne maximum minimum classement ou comparaison.\n"
        "  4 Les montants financiers sont en euros.\n"
        "  5 Si la colonne travaux existe, elle doit être incluse dans les extraits.\n"
        "  6 Si les colonnes client et annee existent, elles doivent être incluses dans les extraits.\n\n"
        "IMPORTANT (TRÈS IMPORTANT)\n"
        "  - Tu ne dois PAS renvoyer des indices de lignes.\n"
        "  - Tu dois renvoyer directement les lignes utilisées dans table_excerpt.rows.\n"
        "  - Chaque élément de table_excerpt.rows doit être une LIGNE EXACTE telle qu'elle apparaît dans "
        "DONNEES DE LA TABLE JSON (mêmes colonnes, mêmes valeurs).\n"
        "  - Ne fabrique jamais une row.\n\n"
        "Format de sortie strictement en JSON valide sans texte avant ni après.\n"
        "Schéma attendu\n"
        "{\n"
        '  \"answer\": \"texte en français, 2 à 6 phrases, sans Markdown, sans emojis.\",\n'
        '  \"uses_context\": true ou false,\n'
        '  \"chart\": {\n'
        '    \"type\": \"bar\" | \"horizontal_bar\" | \"line\" | \"pie\" | \"bubble\" | \"none\",\n'
        '    \"title\": \"Titre lisible pour le graphique\",\n'
        '    \"x_label\": \"Nom de l\'axe X\",\n'
        '    \"y_label\": \"Nom de l\'axe Y\",\n'
        '    \"series\": [\n'
        '      { \"label\": \"nom de la série\", \"points\": [ {\"x\": \"catégorie\", \"y\": nombre} ] }\n'
        "    ]\n"
        "  },\n"
        '  \"table_excerpt\": {\n'
        '    \"columns\": [\"...\"],\n'
        '    \"rows\": [ {\"col1\": \"...\", \"col2\": 123, ...}, ... ]\n'
        "  }\n"
        "}\n\n"
        "Consignes table_excerpt\n"
        "  - columns: renvoie les noms exacts de toutes les colonnes présentes dans la table.\n"
        "  - rows: renvoie uniquement les lignes réellement utilisées pour répondre (top, filtres, etc.).\n"
        "  - Si aucune ligne pertinente: mets rows = [].\n"
    )

    # 5 Prompt utilisateur avec les données JSON
    user_prompt = (
        "CONTEXTE CONVERSATION résumé des derniers échanges\n"
        f"{history_text}\n\n"
        "QUESTION UTILISATEUR\n"
        f"{q}\n\n"
        "SCHEMA DES COLONNES nom et type\n"
        f"{columns_json}\n\n"
        "DONNEES DE LA TABLE JSON chaque élément est une ligne\n"
        f"{data_json}\n\n"
        "IMPORTANT\n"
        "  Pour table_excerpt.rows, copie/colle exactement les objets-lignes existants dans les DONNEES JSON.\n"
        "  Ne renvoie pas d'indices.\n"
        "Réponds strictement au format JSON demandé.\n"
    )

    client = get_kimi_client()

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_prompt},
    ]

    try:
        completion = client.chat.completions.create(
            model=KIMI_MODEL_SINGLE,
            messages=messages,
            temperature=0.2,
            max_tokens=2500,
        )
    except Exception as e:
        raise HTTPException(500, f"Erreur Kimi finance: {e}")

    msg = completion.choices[0].message

    # Gestion du contenu renvoyé string ou segments
    if isinstance(msg.content, str):
        raw_text = msg.content
    else:
        parts: List[str] = []
        for part in msg.content:
            if isinstance(part, dict) and part.get("type") in ("output_text", "text"):
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        raw_text = " ".join(parts).strip()

    raw_text = (raw_text or "").strip()

    # Parsing JSON robuste
    try:
        obj = json.loads(raw_text)
    except Exception:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(raw_text[start : end + 1])
            except Exception:
                raise HTTPException(500, f"Réponse Kimi finance non JSON: {raw_text[:400]}")
        else:
            raise HTTPException(500, f"Réponse Kimi finance non JSON: {raw_text[:400]}")

    answer = (obj.get("answer") or "").strip() or "Réponse vide."

    chart = obj.get("chart") or {
        "type": "none",
        "title": "",
        "x_label": "",
        "y_label": "",
        "series": [],
    }
    chart = _normalize_chart_axes(chart)

    # Extraction des lignes/colonnes pour le frontend (NOUVEAU: rows directs)
    table_excerpt = obj.get("table_excerpt") or {}
    raw_columns = table_excerpt.get("columns") or []
    raw_rows = table_excerpt.get("rows") or []

    # Colonnes sécurisées: toutes les colonnes du fichier (comme ton ancien code)
    if isinstance(raw_columns, list) and raw_columns:
        cols: List[str] = [c for c in raw_columns if c in df_llm.columns]
        for c in df_llm.columns:
            if c not in cols:
                cols.append(c)
    else:
        cols = list(df_llm.columns)

    # Valider les rows renvoyées: elles doivent exister dans les 200 lignes envoyées
    excerpt_rows: List[Dict[str, Any]] = []
    if isinstance(raw_rows, list) and raw_rows:
        for rr in raw_rows:
            if not isinstance(rr, dict):
                continue
            canon = _canonical_row(rr)
            matched = llm_rows_map.get(canon)
            if matched:
                # on renvoie toutes les colonnes (ou cols) -> ici on renvoie cols
                excerpt_rows.append({c: matched.get(c) for c in cols})

    # Aucun fallback: si le modèle n'a pas fourni de rows exactes, on renvoie []
    return answer, chart, excerpt_rows
