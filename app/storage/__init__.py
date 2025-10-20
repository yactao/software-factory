"""
Stockage applicatif:
- Blob Storage: vérif d'existence et génération d'URL SAS lecture courte.
- Table Storage: historisation légère des conversations (chat history).

Fonctions principales exposées:
- get_blob_service()
- blob_exists(container, blob_path)
- make_sas_url(container, blob_path, minutes=5)
- resolve_blob_with_fallbacks(path, containers, try_docx_pdf=True)

- get_table_service()
- get_chat_table()
- save_chat_event(claims, conversation_id, role, route, message, meta=None)
- list_conversation_events(claims, conversation_id)
- delete_conversation(claims, conversation_id)
"""

from .blob import (
    get_blob_service,
    blob_exists,
    make_sas_url,
    resolve_blob_with_fallbacks,
)

from .tables import (
    get_table_service,
    get_chat_table,
    save_chat_event,
    list_conversation_events,
    delete_conversation,
)
