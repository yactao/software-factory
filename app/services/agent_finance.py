# app/services/agent_finance.py

import json
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

import pandas as pd
from fastapi import HTTPException

from app.core.config import KIMI_MODEL_SINGLE
from app.services.kimi_client import get_kimi_client
from app.services.blob_finance_excel import download_finance_excel_to_temp


def _normalize_chart_axes(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    S'assure que pour les graphiques bar/line horizontaux ou verticaux, on a :
      - x : catégorie (str, ex: nom du magasin)
      - y : valeur numérique (int/float)

    Si le LLM a inversé (x = nombre, y = nom magasin), on swap pour chaque série.
    """

    if not chart:
        return chart

    ctype = chart.get("type")
    if ctype not in ("bar", "horizontal_bar", "line", "bubble"):
        # On laisse tel quel pour les autres types (pie, none, etc.)
        return chart

    series = chart.get("series") or []
    for serie in series:
        points = serie.get("points") or []
        if not points:
            continue

        # On regarde si la majorité des points ont x numérique et y string
        num_x = sum(isinstance(p.get("x"), (int, float)) for p in points)
        str_y = sum(isinstance(p.get("y"), str) for p in points)

        if num_x >= len(points) / 2 and str_y >= len(points) / 2:
            # Cas typique : { "x": 2060, "y": "IDF - PARIS ..." }
            # On inverse x et y pour toute la série
            for p in points:
                p["x"], p["y"] = p.get("y"), p.get("x")

    return chart


def answer_finance_with_kimi(
    question: str,
    history_pairs: List[Dict[str, str]],
) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Analyse le fichier Excel finance avec Kimi.

    Retourne:
      - answer_text: réponse en texte brut
      - chart: dict décrivant le graphique à afficher côté frontend
      - excerpt_rows: liste de lignes (dict) extraites du DataFrame, pour affichage dans le frontend
    """

    q = (question or "").strip()
    if not q:
        raise HTTPException(400, "Question vide.")

    # 1) Télécharger l'Excel depuis Azure Blob
    try:
        xlsx_path = download_finance_excel_to_temp()
    except Exception as e:
        raise HTTPException(
            500,
            f"Erreur lors du chargement du fichier Excel finance: {e}",
        )

    # 2) Charger l'Excel côté backend (pandas)
    try:
        df = pd.read_excel(xlsx_path)
    except Exception as e:
        raise HTTPException(500, f"Erreur lecture Excel finance: {e}")

    if df.empty:
        raise HTTPException(500, "Le fichier Excel finance est vide.")

    # On limite le nombre de lignes envoyées au LLM pour éviter un prompt énorme
    MAX_ROWS_FOR_LLM = 200
    df_llm = df.head(MAX_ROWS_FOR_LLM).copy()

    # Conversion en JSON (liste de lignes)
    records = df_llm.to_dict(orient="records")
    data_json = json.dumps(records, ensure_ascii=False)

    # On ajoute aussi la liste des colonnes pour que le modèle comprenne bien
    columns_info: List[Dict[str, Any]] = []
    for col in df_llm.columns:
        col_type = str(df_llm[col].dtype)
        columns_info.append({"name": col, "dtype": col_type})

    columns_json = json.dumps(columns_info, ensure_ascii=False)

    # 3) Historique compact (comme pour /api/rag)
    hist_lines: List[str] = []
    for pair in history_pairs[-3:]:
        u = (pair.get("user") or "").strip()
        a = (pair.get("assistant") or "").strip()
        if u:
            hist_lines.append(f"U: {u}")
        if a:
            hist_lines.append(f"A: {a}")
    history_text = "\n".join(hist_lines) if hist_lines else "aucun historique pertinent."

    # 4) Prompt système orienté data/finance
    system_content = (
        "Tu es un expert data analyst et finance pour le client MDM (Maisons du Monde).\n"
        "Tu disposes d'une table de magasins issue d'un fichier Excel avec des colonnes, par exemple:\n"
        "  magasin: nom du magasin\n"
        "  dept: code du département\n"
        "  PV: montant en euros d'une petite visite (visite de maintenance préventive)\n"
        "  GV: montant en euros d'une grande visite (visite de maintenance plus lourde)\n"
        "  VE: nombre de visites d'entretien annuelles\n"
        "D'autres colonnes peuvent exister, tu dois les interpréter logiquement.\n\n"
        "Chaque magasin peut avoir jusqu'à 3 pv différents ou identiques.\n\n"
        "Règles importantes:\n"
        "  1) Tu réponds STRICTEMENT à partir des données de la table fournie.\n"
        "  2) Si une information n'est pas présente ou pas déductible, tu le dis clairement.\n"
        "  3) Tu peux faire des calculs simples (somme, moyenne, max, min, classement, comparaison) sur les colonnes numériques.\n"
        "  4) Les montants financiers sont en euros (€).\n"
        "  5) VE représente le nombre de visites effectuées, tu peux en déduire des coûts annuels PV*VE, GV*VE, etc. si c'est cohérent.\n\n"
        " 6) Tres important que le y genere soit toujours un nombre (int ou float) pour les graphiques bar/line.\n\n"
        "Tu dois répondre comme un expert finance qui commente les chiffres et explique les résultats.\n\n"
        "Format de sortie STRICTEMENT en JSON valide, sans texte avant ni après.\n"
        "Schéma attendu:\n"
        "{\n"
        '  \"answer\": \"texte en français, 2 à 6 phrases, sans Markdown, sans emojis.\",\n'
        '  \"uses_context\": true ou false,\n'
        '  \"chart\": {\n'
        '    \"type\": \"bar\" | \"horizontal_bar\" | \"line\" | \"pie\" | \"bubble\" | \"none\",\n'
        '    \"title\": \"Titre lisible pour le graphique\",\n'
        '    \"x_label\": \"Nom de l\'axe X\",\n'
        '    \"y_label\": \"Nom de l\'axe Y\",\n'
        '    \"series\": [\n'
        '      {\n'
        '        \"label\": \"nom de la série (ex: Coût annuel PV)\",\n'
        '        \"points\": [\n'
        '          { \"x\": \"valeur X (ex: nom du magasin ou code dept)\", \"y\": nombre },\n'
        '          ...\n'
        '        ]\n'
        '      }\n'
        '    ]\n'
        '  },\n'
        '  \"table_excerpt\": {\n'
        '    \"row_indices\": [0, 2, 5],\n'
        '    \"columns\": [\"magasin\", \"code_magasin\", \"dept\", \"ve_an\", \"montant_annuel\", \"gv\", \"pv\"]\n'
        "  }\n"
        "}\n\n"
        "Consignes pour le champ chart:\n"
        "  - Si la question se prête à un graphique (comparaison entre magasins, évolution, répartition…), propose un type pertinent.\n"
        "  - Si aucun graphique n'est utile, mets \"type\": \"none\" et une liste de séries vide.\n"
        "  - Ne renvoie QUE des points basés sur les données fournies.\n"
        "  - Pour les labels X, utilise typiquement le nom du magasin ou le code département ou la valeur convenable.\n"
        "  - Pour le choix de type de graphique tu dois choisir un type adapté à la question.\n\n"
        "Consignes pour le champ table_excerpt:\n"
        "  - \"row_indices\" doit contenir une petite liste d'indices de lignes (0, 1, 2, ...) parmi les lignes de la table envoyée.\n"
        "  - Utilise uniquement des indices valides présents dans les données.\n"
        "  - \"columns\" doit contenir les noms EXACTS de toutes les colonnes de la table même ceux non utilisés en contexte "
        "(par exemple magasin, code_magasin, dept, ve_an, montant_annuel, gv, pv1, pv2, pv3).\n"
        "  - Si tu ne sais pas quelles lignes mettre, laisse row_indices vide.\n"
    )

    # 5) Prompt utilisateur avec les données JSON
    user_prompt = (
        "CONTEXTE CONVERSATION (résumé des derniers échanges):\n"
        f"{history_text}\n\n"
        "QUESTION UTILISATEUR:\n"
        f"{q}\n\n"
        "SCHEMA DES COLONNES (nom + type):\n"
        f"{columns_json}\n\n"
        "DONNEES DE LA TABLE (JSON, chaque élément est une ligne):\n"
        f"{data_json}\n\n"
        "Analyse UNIQUEMENT ces données et réponds strictement au format JSON demandé.\n"
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
        raise HTTPException(500, f"Erreur Kimi (finance): {e}")

    msg = completion.choices[0].message

    # Gestion du contenu renvoyé (string ou segments)
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
                    f"Réponse Kimi finance non JSON: {raw_text[:400]}",
                )
        else:
            raise HTTPException(
                500,
                f"Réponse Kimi finance non JSON: {raw_text[:400]}",
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

    # 🔧 Normalisation de sécurité : corrige les inversions x / y
    chart = _normalize_chart_axes(chart)

    # === Extraction des lignes/colonnes utilisées pour le frontend ===
    table_excerpt = obj.get("table_excerpt") or {}
    raw_indices = table_excerpt.get("row_indices") or []
    raw_columns = table_excerpt.get("columns") or []

    # Sécuriser les indices
    max_index = len(df_llm)
    row_indices: List[int] = []
    for i in raw_indices:
        try:
            i_int = int(i)
        except Exception:
            continue
        if 0 <= i_int < max_index:
            row_indices.append(i_int)

    # Sécuriser les colonnes : toujours TOUTES les colonnes, en mettant
    # d'abord celles demandées par Kimi si elles existent.
    if raw_columns:
        cols: List[str] = [c for c in raw_columns if c in df_llm.columns]
        for c in df_llm.columns:
            if c not in cols:
                cols.append(c)
    else:
        cols = list(df_llm.columns)

    def _serialize_value(v: Any) -> Any:
        """Convertit les valeurs Pandas/Datetime en types JSON-compatibles."""
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
