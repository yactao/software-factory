from typing import Dict, Any, Optional, List

def _build_odata_filter(filters: Optional[Dict[str, Any]]) -> str:
    """
    Construit un filtre OData avec les colonnes du nouvel index:
      - file_name: égalité stricte ou 'startswith' simple
      - chunk_type: égalité stricte (ex: 'paragraph', 'table', 'checkbox')
      - page: entier exact ou intervalle
      - section_path: élément exact dans la collection (pas de contains partiel côté OData)
    """
    if not filters:
        return ""

    def esc(v: Any) -> str:
        return str(v).replace("'", "''")

    clauses: List[str] = []

    # file_name exact
    if "file_name" in filters and filters["file_name"]:
        clauses.append(f"file_name eq '{esc(filters['file_name'])}'")

    # file_name startswith
    if "file_name_prefix" in filters and filters["file_name_prefix"]:
        clauses.append(f"startswith(file_name, '{esc(filters['file_name_prefix'])}')")

    # chunk_type
    if "chunk_type" in filters and filters["chunk_type"]:
        clauses.append(f"chunk_type eq '{esc(filters['chunk_type'])}'")

    # page exacte
    if "page" in filters and filters["page"] is not None:
        try:
            page_val = int(filters["page"])
            clauses.append(f"page eq {page_val}")
        except Exception:
            pass

    # page mini et maxi
    if "page_min" in filters and filters["page_min"] is not None:
        try:
            pmin = int(filters["page_min"])
            clauses.append(f"page ge {pmin}")
        except Exception:
            pass
    if "page_max" in filters and filters["page_max"] is not None:
        try:
            pmax = int(filters["page_max"])
            clauses.append(f"page le {pmax}")
        except Exception:
            pass

    # section_path: match exact sur un élément de la collection
    if "section_exact" in filters and filters["section_exact"]:
        clauses.append(f"'{esc(filters['section_exact'])}' in section_path")

    return " and ".join(clauses)

def _build_odata_filter_trading(filters: Optional[Dict[str, Any]]) -> str:
    """Construit un filtre OData compatible avec l'index idx-oil-demo."""
    if not filters:
        return ""
    def esc(v: str) -> str:
        return str(v).replace("'", "''")

    clauses = []
    if filters.get("path_prefix"):
        p = esc(filters["path_prefix"])
        clauses.append(f"startswith(source_path, '{p}')")
    for f in ("tenant_id","commodity","product_type","region","route","port",
              "operation_type","vessel_class","contract_type","jurisdiction"):
        if filters.get(f) is not None:
            clauses.append(f"{f} eq '{esc(filters[f])}'") 
            
    if filters.get("hedge_instrument"):
        t = esc(filters["hedge_instrument"])
        clauses.append(f"hedge_instruments/any(h: h eq '{t}')")
    return " and ".join(clauses)
