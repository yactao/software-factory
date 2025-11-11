from typing import Dict, Any, Optional, List

def _build_odata_filter(filters: Optional[Dict[str, Any]]) -> str:
    """
    Filtres OData compatibles avec l'index `mdm-audit-cv-index`.
    Champs pris en charge:
      - entity_type: 'audit_pdf' | 'cv'
      - source_container: ex. 'audit', 'ds-cv'
      - file_name: égalité stricte
      - file_name_prefix: startswith(file_name, ...)
      - magasin_name: égalité stricte
      - magasin_name_prefix: startswith(magasin_name, ...)
      - magasin_code: égalité stricte
      - cv_person_name: égalité stricte
      - cv_specialty: égalité stricte
      - extracted_at_ge / extracted_at_le: bornes datetime ISO 8601
    """
    if not filters:
        return ""

    def esc(v: Any) -> str:
        return str(v).replace("'", "''")

    clauses: List[str] = []

    # typage document
    if filters.get("entity_type"):
        clauses.append(f"entity_type eq '{esc(filters['entity_type'])}'")

    # source container
    if filters.get("source_container"):
        clauses.append(f"source_container eq '{esc(filters['source_container'])}'")

    # file_name strict / prefix
    if filters.get("file_name"):
        clauses.append(f"file_name eq '{esc(filters['file_name'])}'")
    if filters.get("file_name_prefix"):
        clauses.append(f"startswith(file_name, '{esc(filters['file_name_prefix'])}')")

    # audit
    if filters.get("magasin_name"):
        clauses.append(f"magasin_name eq '{esc(filters['magasin_name'])}'")
    if filters.get("magasin_name_prefix"):
        clauses.append(f"startswith(magasin_name, '{esc(filters['magasin_name_prefix'])}')")
    if filters.get("magasin_code"):
        clauses.append(f"magasin_code eq '{esc(filters['magasin_code'])}'")

    # cv
    if filters.get("cv_person_name"):
        clauses.append(f"cv_person_name eq '{esc(filters['cv_person_name'])}'")
    if filters.get("cv_specialty"):
        clauses.append(f"cv_specialty eq '{esc(filters['cv_specialty'])}'")

    # dates
    if filters.get("extracted_at_ge"):
        clauses.append(f"extracted_at ge {esc(filters['extracted_at_ge'])}")
    if filters.get("extracted_at_le"):
        clauses.append(f"extracted_at le {esc(filters['extracted_at_le'])}")

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
