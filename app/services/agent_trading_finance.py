# app/services/agent_trading_finance.py
"""
Multi-Excel finance agent: reads ALL .xlsx files from FINANCE_CONTAINER,
builds a single multi-document JSON payload, calls the same LLM provider as finance,
and returns (answer_text, chart, rows) with doc_id on each row. Anti-hallucination
validation ensures returned rows exactly match source data.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.core.config import FINANCE_CONTAINER
from app.services.blob_trading_finance_excel import (
    list_excel_blobs_in_container,
    download_excel_blob_to_temp,
)
from app.services.llm_provider import get_llm_client_and_model, llm_chat_completion_with_client

MAX_ROWS_PER_DOC = 300


def _normalize_chart_axes(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    S'assure que pour les graphiques bar ou line on a
    x = catégorie (texte), y = valeur numérique.
    Si le modèle a inversé, on inverse x et y pour chaque point.
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


def _serialize_value(v: Any) -> Any:
    if isinstance(v, (pd.Timestamp, datetime, date)):
        return v.isoformat()
    try:
        if isinstance(v, float) and pd.isna(v):
            return None
        if pd.isna(v):
            return None
    except TypeError:
        pass
    if isinstance(v, (np.generic,)):
        return v.item()
    return v


def _read_excel_sheet(path: Path) -> pd.DataFrame:
    """Read first non-empty sheet from Excel. Prefer first sheet."""
    try:
        df = pd.read_excel(path)
        df = df.dropna(how="all").reset_index(drop=True)
        if not df.empty:
            return df
    except Exception:
        pass
    try:
        xl = pd.ExcelFile(path)
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet_name)
            df = df.dropna(how="all").reset_index(drop=True)
            if not df.empty:
                return df
    except Exception:
        pass
    return pd.DataFrame()


def answer_trading_finance_with_kimi(
    question: str,
    history_pairs: List[Dict[str, str]],
) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], List[str]]:
    """
    Analyse tous les fichiers Excel du container finance (multi-document).
    Returns (answer_text, chart, excerpt_rows, columns) with doc_id on each row.
    Rows are validated against source data (anti-hallucination).
    columns = ordre des colonnes pour l'affichage (table_excerpt.columns ou clés de la première row).
    """
    q = (question or "").strip()
    if not q:
        raise HTTPException(400, "Question vide.")

    container = (FINANCE_CONTAINER or "").strip()
    if not container:
        raise HTTPException(500, "FINANCE_CONTAINER non configuré.")

    # 1) List .xlsx blobs
    try:
        blob_names = list_excel_blobs_in_container(container)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erreur liste blobs Excel: {e}")

    if not blob_names:
        raise HTTPException(
            500,
            f"Aucun fichier .xlsx trouvé dans le container '{container}'.",
        )

    # 2) Load each Excel into a doc payload; collect errors
    docs_payload: List[Dict[str, Any]] = []
    temp_paths: List[Path] = []
    parse_errors: List[str] = []

    for blob_name in blob_names:
        try:
            path = download_excel_blob_to_temp(container, blob_name)
            temp_paths.append(path)
        except Exception as e:
            parse_errors.append(f"{blob_name}: téléchargement — {e}")
            continue

        try:
            df = _read_excel_sheet(path)
            if df.empty:
                parse_errors.append(f"{blob_name}: feuille vide")
                continue
            df_llm = df.head(MAX_ROWS_PER_DOC).copy()
            records = df_llm.to_dict(orient="records")
            columns_info: List[Dict[str, Any]] = []
            for col in df_llm.columns:
                columns_info.append({"name": col, "dtype": str(df_llm[col].dtype)})
            docs_payload.append({
                "doc_id": blob_name,
                "columns": columns_info,
                "rows": records,
            })
        except Exception as e:
            parse_errors.append(f"{blob_name}: lecture — {e}")
        # Temp file can be removed after pandas read
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass

    for p in temp_paths:
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass

    if not docs_payload:
        raise HTTPException(
            500,
            "Aucun fichier Excel valide chargé. Erreurs: " + "; ".join(parse_errors[:5]),
        )

    # 3) Build per-doc canonical row maps for validation (doc_id -> canon -> normalized row)
    def _canonical_row(d: Dict[str, Any], columns: List[str]) -> str:
        normalized = {c: _serialize_value(d.get(c)) for c in columns}
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    doc_columns: Dict[str, List[str]] = {}
    doc_rows_map: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for doc in docs_payload:
        doc_id = doc["doc_id"]
        rows = doc.get("rows") or []
        cols = [ci["name"] for ci in (doc.get("columns") or [])]
        if not cols and rows:
            cols = list(rows[0].keys()) if rows else []
        doc_columns[doc_id] = cols
        doc_rows_map[doc_id] = {}
        for r in rows:
            canon = _canonical_row(r, cols)
            if canon not in doc_rows_map[doc_id]:
                doc_rows_map[doc_id][canon] = {c: _serialize_value(r.get(c)) for c in cols}

    # 4) Prompt: multi-document JSON
    donnes_json = json.dumps(docs_payload, ensure_ascii=False, indent=2)
    hist_lines: List[str] = []
    for pair in history_pairs[-3:]:
        u = (pair.get("user") or "").strip()
        a = (pair.get("assistant") or "").strip()
        if u:
            hist_lines.append(f"U: {u}")
        if a:
            hist_lines.append(f"A: {a}")
    history_text = "\n".join(hist_lines) if hist_lines else "aucun historique pertinent."

    system_content = (
        "Tu es un expert data analyst et finance pour un client de la grande distribution.\n"
        "Tu disposes de PLUSIEURS tables Excel (plusieurs documents), chacune avec un doc_id (nom du fichier).\n\n"
        "Règles importantes\n"
        "  1 Tu réponds strictement à partir des données des tables fournies.\n"
        "  2 Si une information n'est pas présente ou pas déductible tu le dis clairement.\n"
        "  3 Tu peux faire des calculs simples (somme, moyenne, max, min, classement, comparaison).\n"
        "  4 Les montants financiers sont en dollars.\n"
        "  5 Chaque ligne dans table_excerpt.rows DOIT contenir le champ \"doc_id\" (nom du fichier source).\n"
        "  6 Chaque ligne doit être une LIGNE EXACTE issue des DONNEES JSON (même doc_id, mêmes colonnes, mêmes valeurs).\n\n"
        "IMPORTANT (TRÈS IMPORTANT)\n"
        "  - Tu ne dois PAS renvoyer des indices de lignes.\n"
        "  - Tu renvoies les lignes utilisées dans table_excerpt.rows.\n"
        " - Tu reponds avec la langue française ou anglaise selon la question posée.\n"
        "  - Chaque élément de table_excerpt.rows doit inclure \"doc_id\" et les colonnes exactes du document concerné.\n"
        "  - Ne fabrique jamais une row.\n\n"
        "Format de sortie strictement en JSON valide sans texte avant ni après.\n"
        "Schéma attendu\n"
        "{\n"
        '  \"answer\": \"texte en 2 à 6 phrases, sans Markdown, sans emojis.\",\n'
        '  \"uses_context\": true ou false,\n'
        '  \"chart\": {\n'
        '    \"type\": \"bar\" | \"horizontal_bar\" | \"line\" | \"pie\" | \"bubble\" | \"none\",\n'
        '    \"title\": \"Titre\", \"x_label\": \"...\", \"y_label\": \"...\",\n'
        '    \"series\": [ { \"label\": \"...\", \"points\": [ {\"x\": \"...\", \"y\": number} ] } ]\n'
        "  },\n"
        '  \"table_excerpt\": {\n'
        '    \"columns\": [\"doc_id\", \"col1\", \"col2\", ...],\n'
        '    \"rows\": [ {\"doc_id\": \"fichier.xlsx\", \"col1\": ..., ...}, ... ]\n'
        "  }\n"
        "}\n\n"
        "Consignes table_excerpt (OBLIGATOIRE quand tu utilises les données)\n"
        "  - columns: inclure \"doc_id\" en premier puis les noms des colonnes utilisées.\n"
        "  - rows: tu DOIS renseigner les lignes exactes des DONNEES JSON sur lesquelles tu t'appuies pour ta réponse et ton graphique.\n"
        "  - Copie exactement les objets-lignes du JSON (mêmes clés, mêmes valeurs); ajoute doc_id si absent.\n"
        "  - Si tu cites des chiffres, des grades, des zones, des cargaisons: ces lignes doivent apparaître dans table_excerpt.rows.\n"
        "  - Si vraiment aucune ligne n'est utilisée: mets rows = [].\n"
    )

    user_prompt = (
        "CONTEXTE CONVERSATION\n"
        f"{history_text}\n\n"
        "QUESTION UTILISATEUR\n"
        f"{q}\n\n"
        "DONNEES JSON (liste de documents; chaque document a doc_id, columns, rows)\n"
        f"{donnes_json}\n\n"
        "IMPORTANT: Pour table_excerpt.rows, copie exactement les objets-lignes des DONNEES JSON en ajoutant doc_id si absent.\n"
        "Réponds strictement au format JSON demandé.\n"
    )

    client, model = get_llm_client_and_model("finance")
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw_text = llm_chat_completion_with_client(
            client, model, messages, temperature=0.2, max_tokens=2500,
        )
    except Exception as e:
        raise HTTPException(500, f"Erreur LLM trading finance: {e}")

    raw_text = (raw_text or "").strip()

    # 5) Robust JSON parse
    try:
        obj = json.loads(raw_text)
    except Exception:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(raw_text[start : end + 1])
            except Exception:
                raise HTTPException(500, f"Réponse LLM non JSON: {raw_text[:400]}")
        else:
            raise HTTPException(500, f"Réponse LLM non JSON: {raw_text[:400]}")

    answer = (obj.get("answer") or "").strip() or "Réponse vide."
    chart = obj.get("chart") or {
        "type": "none", "title": "", "x_label": "", "y_label": "", "series": [],
    }
    chart = _normalize_chart_axes(chart)

    table_excerpt = obj.get("table_excerpt") or {}
    raw_columns = table_excerpt.get("columns") or []
    raw_rows = table_excerpt.get("rows") or []

    # 6) Validate rows: must match source per doc_id; include doc_id in output
    excerpt_rows: List[Dict[str, Any]] = []
    if isinstance(raw_rows, list) and raw_rows:
        for rr in raw_rows:
            if not isinstance(rr, dict):
                continue
            doc_id = rr.get("doc_id")
            if doc_id not in doc_rows_map:
                continue
            cols = doc_columns.get(doc_id, [])
            canon = _canonical_row(rr, cols)
            matched = doc_rows_map[doc_id].get(canon)
            if matched:
                out_row: Dict[str, Any] = {"doc_id": doc_id}
                for c in cols:
                    out_row[c] = matched.get(c)
                excerpt_rows.append(out_row)

    # Colonnes pour l'affichage: ordre du LLM ou clés de la première ligne
    columns: List[str] = []
    if raw_columns and isinstance(raw_columns, list):
        columns = [str(c) for c in raw_columns]
    elif excerpt_rows:
        columns = list(excerpt_rows[0].keys())

    return answer, chart, excerpt_rows, columns
