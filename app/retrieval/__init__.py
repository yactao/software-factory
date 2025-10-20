"""
Récupération (retrieval) et ranking pour le RAG.

Expose:
- AzureSearch: client générique Azure AI Search
- build_odata: construction de filtres OData
- in_scope: test de pertinence minimale
- best_answers: utilitaire pour trier les @search.answers
"""

from .search_client import AzureSearch
from .filters import build_odata
from .rank import in_scope, best_answers
