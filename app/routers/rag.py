from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional, Tuple
import re
import unicodedata
import urllib.parse
from ..services.blob_sas import _blob_exists, _make_sas_url

from ..core.security import _auth_dependency, _require_scope
from ..core.config import RETRIEVAL_K, TOPN_MAX
from ..models.schemas import RAGRequest
from ..services.history_helpers import _save_chat_event, _get_last_qna_pairs
from ..services.search_azure import _search_docs
from ..services.gemini_rag import _synthesize_with_citations
from ..utils.snippets import (
    _extract_path,
    _extract_title,
    _is_in_scope,
    _make_used_doc_from_context,
    _prefer_answer_or_focused_snippet,
)
from ..utils.query_refiner import _compose_search_query_from_history
from ..services.agents_classif import decide_scope_with_kimi
    # scope: "single_store" | "global" | "fallback"
from ..services.agent_global_audit import answer_global_with_kimi

router = APIRouter()
SMALLTALK_RE = re.compile(r"^\s*(bonjour|bonsoir|salut|slt|hello|hi)\b", re.I)


def _norm(s: Optional[str]) -> str:
  if not s:
      return ""
  s = unicodedata.normalize("NFKD", s)
  s = "".join(ch for ch in s if not unicodedata.combining(ch))
  return re.sub(r"\s+", " ", s).strip().lower()


STORE_CODE_RE = re.compile(r"(^|[\s\-_/])(\d{2,6})(\b|$)")


def _extract_store_hints(question: str) -> Tuple[Optional[str], Optional[str]]:
  qn = _norm(question)

  m = STORE_CODE_RE.search(qn)
  code_hint = m.group(2) if m else None

  tmp = re.sub(r"\d{2,6}", " ", qn)
  tmp = re.sub(r"\b(magasin|photo|photos|images?|donne|moi|de|du|les|la|le|des|pour|mdm)\b", " ", tmp)
  name_hint = re.sub(r"[^a-z0-9\s\-]", " ", tmp)
  name_hint = re.sub(r"\s+", " ", name_hint).strip()

  if len(name_hint) < 3:
      name_hint = None

  return (name_hint, code_hint)


def _doc_matches_store(d: Dict[str, Any], name_hint: Optional[str], code_hint: Optional[str]) -> bool:
  name = _norm(d.get("magasin_name") or "")
  code = str(d.get("magasin_code") or "").strip()
  file_name = _norm(d.get("file_name") or "")

  ok = False
  if code_hint and code and code == code_hint:
      ok = True

  if not ok and name_hint:
      tokens = [t for t in (name_hint or "").split() if len(t) >= 3]
      if tokens:
          if all(t in name for t in tokens) or all(t in file_name for t in tokens):
              ok = True

  return ok

def _extract_blob_path_from_url(url: str, container: str | None = None) -> Optional[str]:
    """
    À partir d'une URL de blob (avec SAS), extrait le chemin du blob
    sans le container ni la query-string.

    Ex:
      url = https://acc.blob.core.windows.net/auditimage/62_idf_paris...png?se=...
      container = "auditimage"
      -> "62_idf_paris_428_428_idf_paris_photo_1.png"
    """
    if not url:
        return None

    try:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or ""
        path = path.lstrip("/")  # "auditimage/xxx.png"

        # Si on connaît le container, on le retire explicitement
        if container:
            prefix = f"{container}/"
            if path.startswith(prefix):
                path = path[len(prefix):]
        else:
            # Sinon, on retire le premier segment "container/"
            parts = path.split("/", 1)
            if len(parts) == 2:
                path = parts[1]

        if not path:
            return None

        return path
    except Exception:
        return None


def _guess_images_from_file_pattern(
    d: Dict[str, Any],
    container: str,
    limit: int,
) -> List[str]:
    """
    Pour les documents où image_blob_urls est vide mais où les images existent
    probablement dans le container (ex: auditimage), on essaie de reconstruire
    le pattern du nom du fichier à partir de file_name.

    Ex:
      file_name:  "43_38_mdm_paradis_041_041_mdm_paradis.pdf"
      pattern img: "38_mdm_paradis_041_041_mdm_paradis_photo_1.png"

    On teste quelques candidats: ..._photo_1.png, ..._photo_2.png, etc.
    """
    images: List[str] = []
    file_name = (d.get("file_name") or "").strip()
    if not file_name or not container or limit <= 0:
        return images

    base = file_name.rsplit(".", 1)[0]  # sans .pdf
    parts = base.split("_")

    if len(parts) >= 3:
        # on enlève le premier numéro (index DOC), on garde fiche + reste
        # 22_17_mdm_dijon... -> fiche = 17, rest = mdm_dijon...
        fiche = parts[1]
        rest = "_".join(parts[2:])
        prefix = f"{fiche}_{rest}_photo_"
    else:
        # fallback: on tente base_photo_N
        prefix = base + "_photo_"

    # on teste quelques noms raisonnables
    max_photos = min(max(limit, 1), 20)
    exts = ["png", "jpg", "jpeg"]

    for i in range(1, max_photos + 1):
        for ext in exts:
            blob_path = f"{prefix}{i}.{ext}"
            if _blob_exists(container, blob_path):
                sas = _make_sas_url(container, blob_path, minutes=60)
                if sas:
                    images.append(sas)
            if len(images) >= limit:
                return images

    return images
def _gather_images_for_store(
  hits: List[Dict[str, Any]],
  name_hint: Optional[str],
  code_hint: Optional[str],
  limit: int,
) -> List[str]:
  """
  Retourne une liste d'URL d'images avec SAS VALIDE:

    1) Si image_blob_urls est renseigné dans l'index:
       - on extrait le chemin du blob
       - on régénère un SAS frais avec _make_sas_url

    2) Si image_blob_urls est vide mais image_blob_container + file_name existent:
       - on tente de deviner les noms des images à partir du pattern de file_name
       - on teste l'existence des blobs dans le container
       - on génère les SAS correspondants

  Tout est dédupliqué et limité à `limit`.
  """

  images: List[str] = []

  if limit <= 0:
      return images

  for d in hits:
      if not _doc_matches_store(d, name_hint, code_hint):
          continue

      container = d.get("image_blob_container") or ""
      container = container.strip()
      if not container:
          # pas de container image → on ne tente rien pour ce doc
          continue

      # ----- Cas 1 : URLs déjà présentes dans l'index -----
      urls = d.get("image_blob_urls") or []
      if isinstance(urls, list) and urls:
          for u in urls:
              if not isinstance(u, str) or not u:
                  continue
              blob_path = _extract_blob_path_from_url(u, container)
              if not blob_path:
                  continue
              sas = _make_sas_url(container, blob_path, minutes=60)
              if sas:
                  images.append(sas)
              if len(images) >= limit:
                  break

      if len(images) >= limit:
          break

      # ----- Cas 2 : aucune URL en index → on tente de deviner les noms -----
      if (not urls) and d.get("file_name"):
          extra = _guess_images_from_file_pattern(
              d,
              container=container,
              limit=limit - len(images),
          )
          images.extend(extra)

      if len(images) >= limit:
          break

  # Déduplication en conservant l'ordre
  seen = set()
  uniq: List[str] = []
  for u in images:
      if u not in seen:
          uniq.append(u)
          seen.add(u)

  return uniq[:limit]


def _model_name_for_scope(scope: str) -> str:
  """
  Retourne le nom marketing du modèle / agent pour la réponse.
  - scope == 'global' -> analyse globale du PDF d'audit
  - sinon -> RAG fiche magasin / fallback
  """
  if scope == "global":
      return "Aïna Deep Search"   # analyse globale
  else:
      return "Aïna Instant"       # RAG fiche / fallback


@router.post("/api/rag")
def rag(req: RAGRequest, claims: Dict[str, Any] = Depends(_auth_dependency)):
  _require_scope(claims)

  question = (req.question or "").strip()
  if not question:
      raise HTTPException(400, "Question is empty.")

  # 0) Enregistrement du message utilisateur
  conv_id = _save_chat_event(
      claims,
      req.conversation_id,
      role="user",
      route="rag",
      message=question,
      meta={"filters": req.filters, "top_k": req.top_k},
  )

  # 0-bis) Small talk → réponse courte et sortie immédiate
  if SMALLTALK_RE.search(question):
      model_name = "Aïna Instant"  # ou un autre label générique si tu préfères
      payload = {
          "answer": "Bonjour. Posez une question liée à vos documents pour que je puisse répondre.",
          "citations": [],
          "used_docs": [],
          "conversation_id": conv_id,
          "model": model_name,
      }
      _save_chat_event(
          claims,
          conv_id,
          role="assistant",
          route="rag",
          message=payload["answer"],
          meta=payload,
      )
      return payload

  # 0-ter) Décision de portée via Kimi: single_store / global / fallback
  try:
      scope, scope_reason = decide_scope_with_kimi(question)
  except Exception:
      scope, scope_reason = "fallback", "error"

  # Nom du modèle / agent selon la portée
  model_name = _model_name_for_scope(scope)

  # 0-quater) Si la question est globale, on bypasse toute la partie RAG Azure
  if scope == "global":
      # Agent global: envoie le PDF global à Kimi et récupère la réponse
      answer_text, uses_context = answer_global_with_kimi(question)

      resp_payload = {
          "answer": answer_text,
          "citations": [],
          "used_docs": [],
          "conversation_id": conv_id,
          "images": [],
          "model": model_name,  
      }

      _save_chat_event(
          claims,
          conv_id,
          role="assistant",
          route="rag",
          message=resp_payload["answer"],
          meta={**resp_payload, "scope": scope, "scope_reason": scope_reason},
      )
      return resp_payload

  # À partir d’ici: chemin normal RAG "single fiche" (ou fallback)
  # 1) Historique
  try:
      history_pairs = _get_last_qna_pairs(claims, conv_id, route="rag", max_pairs=3)
      if history_pairs and history_pairs[-1].get("user", "").strip() == question:
          history_pairs = history_pairs[:-1]
  except Exception:
      history_pairs = []

  # 2) Raffinement de la requête avec historique
  effective_question, refine_meta = _compose_search_query_from_history(question, history_pairs)
  try:
      _save_chat_event(
          claims,
          conversation_id=conv_id,
          role="meta",
          route="meta",
          message="",
          meta={
              "type": "query_refined",
              "original": question,
              "refined": effective_question,
              **refine_meta,
              "scope": scope,
              "scope_reason": scope_reason,
              "model": model_name,
          },
      )
  except Exception:
      pass

  # 3) Search Azure
  search_json = _search_docs(effective_question, req.filters, k=RETRIEVAL_K)
  hits = search_json.get("value", []) or []
  answers = search_json.get("@search.answers", []) or []

  if not _is_in_scope(hits) and not answers:
      payload = {
          "answer": "Je ne trouve pas d’information pertinente dans les documents fournis pour cette question.",
          "citations": [],
          "used_docs": [],
          "conversation_id": conv_id,
          "model": model_name,  
      }
      _save_chat_event(
          claims,
          conv_id,
          role="assistant",
          route="rag",
          message=payload["answer"],
          meta={**payload, "scope": scope, "scope_reason": scope_reason},
      )
      return payload

  # 4) Construction des contextes LLM
  N = max(1, min(req.top_k or TOPN_MAX, TOPN_MAX))
  contexts: List[Dict[str, Any]] = []

  # 4-a) Réponses directes (si answers Azure)
  if answers:
      try:
          answers_sorted = sorted(answers, key=lambda a: a.get("score", 0), reverse=True)
      except Exception:
          answers_sorted = answers
      best_ans = answers_sorted[0]
      ans_text = (best_ans.get("text") or "").strip()
      if ans_text:
          contexts.append(
              {
                  "title": "Azure AI Search — Réponse",
                  "snippet": ans_text,
                  "meta": {
                      "kind": "answer",
                      "key": best_ans.get("key"),
                      "score": best_ans.get("score"),
                  },
              }
          )

  # 4-b) Documents
  for d in hits[:N]:
      doc_title = _extract_title(d)
      doc_path = _extract_path(d)
      caps = d.get("@search.captions") or []
      cap_text = caps[0].get("text") if caps else ""
      snippet = (
          (cap_text + "\n" + (d.get("content") or ""))[:1800]
          if cap_text
          else _prefer_answer_or_focused_snippet(effective_question, d)
      )
      contexts.append(
          {
              "title": doc_title,
              "snippet": snippet,
              "meta": {
                  "id": d.get("id"),
                  "path": doc_path,
                  "score": d.get("@search.score"),
                  "reranker": d.get("@search.rerankerScore"),
              },
          }
      )

  # 5) Synthèse texte (RAG single fiche, via Kimi maintenant)
  answer_text, uses_context, used_list = _synthesize_with_citations(
      question=question,
      contexts=contexts,
      chat_history_pairs=history_pairs,
  )

  def _is_doc_context(c: Dict[str, Any]) -> bool:
      return c.get("meta", {}).get("kind") != "answer"

  # 5-bis) Construction des used_docs
  if used_list:
      selected = []
      for i in used_list:
          if 1 <= i <= len(contexts):
              c = contexts[i - 1]
              if _is_doc_context(c):
                  selected.append(c)
      used_docs = [_make_used_doc_from_context(c) for c in selected]
  elif uses_context:
      doc_contexts = [c for c in contexts if _is_doc_context(c)]
      selected = doc_contexts[: min(3, len(doc_contexts))]
      used_docs = [_make_used_doc_from_context(c) for c in selected]
  else:
      used_docs = []

  # 6) Extraction d’images ciblées magasin
  name_hint, code_hint = _extract_store_hints(question)
  images: List[str] = []
  if name_hint or code_hint:
      img_limit = max(1, min(req.top_k or 30, 200))
      images = _gather_images_for_store(hits, name_hint, code_hint, img_limit)

  # 7) Payload final
  final_answer = answer_text
  if images:
      label = ""
      if code_hint and name_hint:
          label = f" pour « {name_hint} » (code {code_hint})"
      elif code_hint:
          label = f" pour le code {code_hint}"
      elif name_hint:
          label = f" pour « {name_hint} »"
      final_answer = f"J’ai trouvé {len(images)} image(s){label}."

  resp_payload = {
      "answer": final_answer,
      "citations": [],
      "used_docs": used_docs,
      "conversation_id": conv_id,
      "images": images,
      "model": model_name,  
  }

  _save_chat_event(
      claims,
      conv_id,
      role="assistant",
      route="rag",
      message=resp_payload["answer"],
      meta={
          **resp_payload,
          "refined_query": effective_question,
          **refine_meta,
          "scope": scope,
          "scope_reason": scope_reason,
      },
  )
  return resp_payload
