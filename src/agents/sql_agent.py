"""Autonomous SQL Agent with schema-grounded generation and up to 3 self-correction loops."""

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from src.agents.llm_provider import LLMProvider, get_llm_provider
from src.warehouse.query_engine import WarehouseQueryEngine, QueryResult
from src.warehouse.catalog import WarehouseCatalog
from src.governance.guardrails import GovernanceGuardrails, GuardrailResult
from src.governance.masking import mask_result_rows
from src.governance.audit import AuditManager, get_audit_manager


@dataclass
class SQLAgentResult:
    """Execution output from the SQL Agent."""
    success: bool
    final_sql: str
    attempts: List[Dict[str, Any]]
    query_result: Optional[QueryResult] = None
    masked_rows: Optional[List[Dict[str, Any]]] = None
    guardrail_result: Optional[GuardrailResult] = None
    audit_id: Optional[str] = None
    error: Optional[str] = None


class SQLAgent:
    """Generates, validates, executes, and self-corrects DuckDB SQL queries."""

    SYSTEM_PROMPT = """You are OrchardIQ's Expert SQL Engineer.
Generate valid, performant DuckDB SQL queries that answer business questions using the provided star-schema data warehouse.

Rules:
1. Output ONLY a valid DuckDB SQL query enclosed inside a ```sql ... ``` code block.
2. Only write SELECT queries or queries starting with WITH (CTEs). Never write INSERT, UPDATE, DELETE, DROP, or ALTER.
3. Tables available in DuckDB Lakehouse:
   - dim_product (product_id, product_name, category, product_line, price_usd, cost_usd, warranty_months, status)
   - dim_store (store_id, store_name, channel, city, state_province, country, region_id, square_feet, opened_date)
   - dim_customer (customer_id, first_name, last_name, email, phone, street_address, city, country, region_id, customer_segment)
   - dim_date (date_id, full_date, day_name, month_number, month_name, calendar_quarter, calendar_year, fiscal_quarter, fiscal_year, is_weekend, is_holiday)
   - dim_region (region_id, region_name, headquarters_city, currency, tax_rate_standard)
   - fact_sales (sale_id, date_id, customer_id, product_id, store_id, region_id, channel, units, unit_price, discount_amount, gross_revenue, net_revenue, cogs, gross_margin, tax_amount, year, month)
   - fact_returns (return_id, sale_id, date_id, customer_id, product_id, store_id, region_id, return_reason, units, refund_amount, restock_status, year, month)
   - fact_support_claims (claim_id, date_id, customer_id, product_id, store_id, region_id, claim_type, claim_status, repair_cost, customer_deductible, turnaround_days, component_batch_id, year, month)
   - fact_marketing_spend (spend_id, date_id, region_id, product_id, channel, spend_usd, impressions, clicks, conversions, year, month)
   - fact_finance_revenue (finance_entry_id, date_id, fiscal_quarter, fiscal_year, region_id, product_line, recognized_net_revenue, deferred_services_revenue, total_gaap_revenue, operating_margin)
4. Partition columns year and month in fact tables are available for high performance predicate pushdown.
5. In DuckDB, if comparing partitioned month, you can use CAST(month AS INTEGER) or direct integers.
6. Always alias aggregated metrics clearly (e.g. net_revenue_usd, total_claims).
"""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        query_engine: Optional[WarehouseQueryEngine] = None,
        guardrails: Optional[GovernanceGuardrails] = None,
        audit_manager: Optional[AuditManager] = None,
        max_retries: int = 3,
    ):
        self.llm = llm_provider or get_llm_provider()
        self.query_engine = query_engine or WarehouseQueryEngine()
        self.guardrails = guardrails or GovernanceGuardrails()
        self.audit_manager = audit_manager or get_audit_manager(conn=self.query_engine.conn)
        self.max_retries = max_retries

    def extract_sql_from_response(self, text: str) -> str:
        """Extract clean SQL string from markdown code block or plain text."""
        match = re.search(r"```(?:sql)?\s*([\s\S]+?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Fallback to cleaning raw text if it starts with SELECT or WITH
        clean = text.strip()
        if clean.upper().startswith("SELECT") or clean.upper().startswith("WITH"):
            return clean
        return clean

    def run(
        self,
        query: str,
        role: str = "analyst",
        session_id: str = "default",
        run_id: str = "default",
        schema_context: Optional[str] = None,
    ) -> SQLAgentResult:
        """Alias for generate_and_execute."""
        return self.generate_and_execute(
            question=query,
            user_role=role,
            session_id=session_id,
            run_id=run_id,
            schema_context=schema_context,
        )

    def generate_and_execute(
        self,
        question: str,
        user_role: str = "analyst",
        session_id: str = "session_default",
        run_id: str = "run_default",
        schema_context: Optional[str] = None,
    ) -> SQLAgentResult:
        """Execute text-to-SQL with up to 3 self-correction iterations on syntax or guardrail failure."""
        # 1. Prompt Injection Pre-check
        is_injection, injection_msg = self.guardrails.check_prompt_injection(question)
        if is_injection:
            audit = self.audit_manager.record_event(
                session_id=session_id,
                run_id=run_id,
                user_role=user_role,
                question=question,
                sql_query="BLOCKED_DUE_TO_INJECTION",
                decision="BLOCKED_PROMPT_INJECTION",
                reason=injection_msg or "Prompt injection rejected",
            )
            return SQLAgentResult(
                success=False,
                final_sql="",
                attempts=[{"attempt": 1, "error": injection_msg, "status": "blocked"}],
                audit_id=audit.audit_id,
                error=injection_msg,
            )

        attempts_log: List[Dict[str, Any]] = []
        current_prompt = f"User Question: {question}\n\nUser Role: {user_role}\n"
        if schema_context:
            current_prompt += f"\nRelevant Schema / Context:\n{schema_context}\n"

        final_sql = ""
        last_error = ""

        for attempt in range(1, self.max_retries + 1):
            t0 = time.perf_counter()
            llm_resp = self.llm.generate(
                prompt=current_prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=0.0,
            )
            candidate_sql = self.extract_sql_from_response(llm_resp.content)
            final_sql = candidate_sql

            # 2. Pre-Execution Guardrails Check (AST Validation + Allowlist)
            guard_res = self.guardrails.validate_sql(candidate_sql, user_role=user_role)

            if not guard_res.is_safe:
                err_msg = f"Governance rejection: {'; '.join(guard_res.violations)}"
                last_error = err_msg
                attempts_log.append({
                    "attempt": attempt,
                    "sql": candidate_sql,
                    "status": "guardrail_rejected",
                    "error": err_msg,
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                })
                # Feed guardrail rejection back for self-correction
                current_prompt += (
                    f"\nAttempt {attempt} SQL:\n{candidate_sql}\n"
                    f"Validation Error:\n{err_msg}\n"
                    f"Please self-correct the SQL to adhere to read-only rules and role '{user_role}' permissions."
                )
                continue

            # 3. Execute Validated SQL in DuckDB
            sanitized_sql = guard_res.sanitized_sql
            final_sql = sanitized_sql
            query_res = self.query_engine.execute_query(sanitized_sql)

            if not query_res.success:
                err_msg = f"DuckDB Execution Error: {query_res.error}"
                last_error = err_msg
                attempts_log.append({
                    "attempt": attempt,
                    "sql": sanitized_sql,
                    "status": "execution_failed",
                    "error": err_msg,
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                })
                # Feed database error back for self-correction
                current_prompt += (
                    f"\nAttempt {attempt} SQL:\n{sanitized_sql}\n"
                    f"Execution Error:\n{err_msg}\n"
                    f"Please fix the DuckDB SQL query syntax, column names, or joins."
                )
                continue

            # 4. Successful Execution -> Apply RBAC Column Masking
            masked_rows = mask_result_rows(query_res.rows, user_role=user_role)
            attempt_latency = round((time.perf_counter() - t0) * 1000, 2)

            attempts_log.append({
                "attempt": attempt,
                "sql": sanitized_sql,
                "status": "succeeded",
                "row_count": len(masked_rows),
                "latency_ms": attempt_latency,
            })

            # 5. Record Immutable Audit Event
            audit = self.audit_manager.record_event(
                session_id=session_id,
                run_id=run_id,
                user_role=user_role,
                question=question,
                sql_query=sanitized_sql,
                decision=guard_res.decision,
                reason=f"Executed successfully in attempt {attempt}",
                tables_accessed=guard_res.tables_referenced,
                row_count=len(masked_rows),
                latency_ms=query_res.latency_ms,
            )

            return SQLAgentResult(
                success=True,
                final_sql=sanitized_sql,
                attempts=attempts_log,
                query_result=query_res,
                masked_rows=masked_rows,
                guardrail_result=guard_res,
                audit_id=audit.audit_id,
                error=None,
            )

        # All retries exhausted
        audit = self.audit_manager.record_event(
            session_id=session_id,
            run_id=run_id,
            user_role=user_role,
            question=question,
            sql_query=final_sql,
            decision="BLOCKED_RETRY_EXHAUSTED",
            reason=f"Failed after {self.max_retries} attempts: {last_error}",
        )

        return SQLAgentResult(
            success=False,
            final_sql=final_sql,
            attempts=attempts_log,
            audit_id=audit.audit_id,
            error=f"Exhausted {self.max_retries} self-correction attempts: {last_error}",
        )
