"""Data Catalog endpoints: GET /catalog/search and GET /catalog/tables."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Query, Depends

from src.rag.retriever import HybridRetriever
from src.warehouse.catalog import WarehouseCatalog
from src.warehouse.query_engine import WarehouseQueryEngine
from src.api.auth import get_current_role

router = APIRouter(prefix="/catalog", tags=["Data Catalog & Knowledge Base"])

retriever = HybridRetriever()
query_engine = WarehouseQueryEngine()
catalog = WarehouseCatalog()


@router.get("/search")
def search_catalog(
    q: str = Query(..., description="Search query across knowledge base, metrics, tickets"),
    doc_type: Optional[str] = Query(None, description="Optional filter by doc_type"),
    top_k: int = Query(5, description="Number of results to return"),
    role: str = Depends(get_current_role),
):
    """Search knowledge base docs, metric glossary, and support tickets."""
    results = retriever.retrieve(query=q, top_k=top_k, doc_type=doc_type)
    return {
        "query": q,
        "count": len(results),
        "results": [r.to_dict() for r in results],
    }


@router.get("/tables")
def list_warehouse_tables(role: str = Depends(get_current_role)):
    """List all star-schema warehouse tables, schemas, and governance classifications."""
    tables = [
        "dim_product", "dim_store", "dim_customer", "dim_date", "dim_region",
        "fact_sales", "fact_returns", "fact_support_claims", "fact_marketing_spend", "fact_finance_revenue"
    ]

    schema_info = []
    for tbl in tables:
        cols = catalog.get_table_columns(tbl)
        # Check if table has restricted columns for the role
        has_pii = tbl == "dim_customer"
        is_finance_restricted = tbl == "fact_finance_revenue" and role == "analyst"
        schema_info.append({
            "table_name": tbl,
            "type": "dimension" if tbl.startswith("dim") else "fact",
            "columns": cols,
            "has_restricted_pii": has_pii,
            "role_accessible": not is_finance_restricted,
            "governance_tag": "Restricted-Finance" if is_finance_restricted else ("Restricted-PII" if has_pii else "Public-Enterprise"),
        })

    return {"tables": schema_info}
