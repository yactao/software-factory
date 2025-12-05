# app/services/agent_vet_finance.py

import json
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import pandas as pd
from fastapi import HTTPException

from app.core.config import KIMI_MODEL_SINGLE
from app.services.kimi_client import get_kimi_client
from app.services.blob_vet_finance_excel import download_vet_finance_excel_to_temp


def _normalize_chart_axes(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise les axes pour les graphiques bar ou line.

    Objectif:
      x doit représenter une catégorie (texte)
      y doit représenter une valeur numérique
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


def answer_vet_finance_with_kimi(
    question: str,
    history_pairs: List[Dict[str, str]],
) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Analyse un Excel Vet Finance avec trois feuilles:
      Mensuel, Annuel, Prévisions.

    Retour:
      answer_text: explication en texte
      chart: configuration de graphique
      excerpt_rows: lignes extraites pour le frontend
    """

    q = (question or "").strip()
    if not q:
        raise HTTPException(400, "Question vide.")

    # 1) Télécharger le fichier Excel Vet Finance depuis Azure Blob
    try:
        xlsx_path = download_vet_finance_excel_to_temp()
    except Exception as e:
        raise HTTPException(
            500,
            f"Erreur lors du chargement du fichier Excel Vet Finance: {e}",
        )

    # 2) Lecture des trois feuilles et fusion
    try:
        df_mensuel = pd.read_excel(xlsx_path, sheet_name="Mensuel")
        df_annuel = pd.read_excel(xlsx_path, sheet_name="Annuel")
        df_prev = pd.read_excel(xlsx_path, sheet_name="Prévisions")

        df_mensuel["table"] = "Mensuel"
        df_annuel["table"] = "Annuel"
        df_prev["table"] = "Prévisions"

        df = pd.concat([df_mensuel, df_annuel, df_prev], ignore_index=True)
        df = df.dropna(how="all").reset_index(drop=True)
    except Exception as e:
        raise HTTPException(500, f"Erreur lecture Excel Vet Finance: {e}")

    if df.empty:
        raise HTTPException(500, "Le fichier Excel Vet Finance est vide.")

    # On limite le volume envoyé au LLM
    MAX_ROWS_FOR_LLM = 300
    df_llm = df.head(MAX_ROWS_FOR_LLM).copy()

    nb_rows = len(df_llm)
    row_indices_hint = (
        f"Tu disposes de {nb_rows} lignes indexées de 0 à {nb_rows - 1}. "
        "Les indices valides pour table_excerpt.row_indices doivent être dans cette plage. "
        "Si tu ne sais pas quelles lignes choisir, utilise par défaut [0, 1, 2, 3, 4] si elles existent."
    )

    # Conversion en JSON de la table fusionnée
    records = df_llm.to_dict(orient="records")
    data_json = json.dumps(records, ensure_ascii=False)

    # Informations sur les colonnes
    columns_info: List[Dict[str, Any]] = []
    for col in df_llm.columns:
        col_type = str(df_llm[col].dtype)
        columns_info.append({"name": col, "dtype": col_type})
    columns_json = json.dumps(columns_info, ensure_ascii=False)

    # 3) Historique compact
    hist_lines: List[str] = []
    for pair in history_pairs[-3:]:
        u = (pair.get("user") or "").strip()
        a = (pair.get("assistant") or "").strip()
        if u:
            hist_lines.append(f"U: {u}")
        if a:
            hist_lines.append(f"A: {a}")
    history_text = "\n".join(hist_lines) if hist_lines else "aucun historique pertinent."

    # 4) Prompt system orienté clinique vétérinaire
    system_content = (
        "Tu es un expert en analyse financière pour une clinique vétérinaire.\n"
        "Tu disposes d une table fusionnée issue de trois feuilles Excel:\n"
        "  table = Mensuel: chiffres d activité par mois pour la clinique\n"
        "  table = Annuel: synthèse annuelle par type d activité\n"
        "  table = Prévisions: projections de revenus par mois\n\n"
        "Les colonnes possibles sont par exemple:\n"
        "  Mois: nom du mois ou période\n"
        "  Activité: type d acte vétérinaire (consultation, chirurgie, vaccination, etc.)\n"
        "  Consultations, Chirurgies, Vaccinations, Hospitalisation, Vente produits, Urgences, Divers: montants en euros\n"
        "  Total Annuel (€): total annuel par activité\n"
        "  table: indique si la ligne vient de la partie Mensuel, Annuel ou Prévisions\n\n"
        "Règles importantes:\n"
        "  1) Tu réponds uniquement à partir des données fournies.\n"
        "  2) Si une information n est pas présente tu le dis clairement.\n"
        "  3) Tu peux faire des comparaisons, des classements, des moyennes et des totaux.\n"
        "  4) Les montants financiers sont en euros.\n"
        "  5) Tu expliques les résultats comme un consultant qui conseille la clinique.\n"
        "  6) Pour les graphiques bar et line, la valeur y doit toujours être numérique.\n\n"
        "Format de sortie strictement en JSON valide, sans texte avant ni après.\n"
        "Schéma attendu:\n"
        "{\n"
        '  \"answer\": \"texte en français, 2 à 6 phrases, sans Markdown, sans emojis.\",\n'
        '  \"uses_context\": true ou false,\n'
        '  \"chart\": {\n'
        '    \"type\": \"bar\" | \"horizontal_bar\" | \"line\" | \"pie\" | \"bubble\" | \"none\",\n'
        '    \"title\": \"Titre lisible pour le graphique\",\n'
        '    \"x_label\": \"Nom de l axe X\",\n'
        '    \"y_label\": \"Nom de l axe Y\",\n'
        '    \"series\": [\n'
        '      {\n'
        '        \"label\": \"nom de la série\",\n'
        '        \"points\": [\n'
        '          { \"x\": \"catégorie\", \"y\": nombre },\n'
        '          ...\n'
        '        ]\n'
        '      }\n'
        '    ]\n'
        '  },\n'
        '  \"table_excerpt\": {\n'
        '    \"row_indices\": [0, 2, 5],\n'
        '    \"columns\": [\"Mois\", \"Activité\", \"Consultations\", \"Chirurgies\", \"Total Annuel (€)\", \"table\"]\n'
        "  }\n"
        "}\n\n"
        "Consignes pour chart:\n"
        "  Si la question se prête à une comparaison ou une évolution, choisis un type de graphique adapté.\n"
        "  Si aucun graphique n est pertinent, utilise type = none et une liste de séries vide.\n"
        "Consignes pour table_excerpt:\n"
        "  row_indices doit contenir quelques indices de lignes de la table envoyée.\n"
        "  columns doit contenir des noms de colonnes valides, présents dans la table.\n"
    )

    # 5) Prompt utilisateur avec contexte et données
    user_prompt = (
        "CONTEXTE CONVERSATION:\n"
        f"{history_text}\n\n"
        "QUESTION UTILISATEUR:\n"
        f"{q}\n\n"
        "SCHEMA DES COLONNES (nom et type):\n"
        f"{columns_json}\n\n"
        "DONNEES DE LA TABLE FUSIONNÉE (JSON, chaque élément est une ligne):\n"
        f"{data_json}\n\n"
        "INFORMATION SUR LES INDICES DE LIGNES:\n"
        f"{row_indices_hint}\n\n"
        "Analyse uniquement ces données et réponds strictement au format JSON demandé.\n"
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
            max_tokens=1800,
        )
    except Exception as e:
        raise HTTPException(500, f"Erreur Kimi Vet Finance: {e}")

    msg = completion.choices[0].message

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
                raise HTTPException(
                    500,
                    f"Réponse Kimi Vet Finance non JSON: {raw_text[:400]}",
                )
        else:
            raise HTTPException(
                500,
                f"Réponse Kimi Vet Finance non JSON: {raw_text[:400]}",
            )

    answer = (obj.get("answer") or "").strip()
    if not answer:
        answer = "Réponse vide."

    chart = obj.get("chart") or {
        "type": "none",
        "title": "",
        "x_label": "",
        "y_label": "",
        "series": [],
    }

    chart = _normalize_chart_axes(chart)

    # Extraction des lignes pour le frontend
    table_excerpt = obj.get("table_excerpt") or {}
    raw_indices = table_excerpt.get("row_indices") or []
    raw_columns = table_excerpt.get("columns") or []

    max_index = len(df_llm)

    row_indices: List[int] = []
    for i in raw_indices:
        try:
            i_int = int(i)
        except Exception:
            continue
        if 0 <= i_int < max_index:
            row_indices.append(i_int)

    if not row_indices and max_index > 0:
        row_indices = list(range(min(5, max_index)))

    if isinstance(raw_columns, list) and raw_columns:
        cols: List[str] = [c for c in raw_columns if c in df_llm.columns]
        for c in df_llm.columns:
            if c not in cols:
                cols.append(c)
    else:
        cols = list(df_llm.columns)

    def _serialize_value(v: Any) -> Any:
        if isinstance(v, (pd.Timestamp, datetime, date)):
            return v.isoformat()
        if isinstance(v, float) and pd.isna(v):
            return None
        if pd.isna(v):
            return None
        return v

    excerpt_rows: List[Dict[str, Any]] = []
    for idx in row_indices:
        row_dict: Dict[str, Any] = {}
        for col in cols:
            try:
                value = df_llm.iloc[idx][col]
            except Exception:
                value = None
            row_dict[col] = _serialize_value(value)
        excerpt_rows.append(row_dict)

    return answer, chart, excerpt_rows
