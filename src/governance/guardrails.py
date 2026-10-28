"""Pre-execution SQL AST validation using sqlglot and prompt-injection defense."""

import re
from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Tuple
import sqlglot
from sqlglot import exp


@dataclass
class GuardrailResult:
    """Result of a governance pre-execution evaluation."""
    is_safe: bool
    sanitized_sql: str
    decision: str  # ALLOWED, MUTATED_LIMIT, BLOCKED_UNSAFE_AST, BLOCKED_UNAUTHORIZED_TABLE, BLOCKED_INJECTION
    violations: List[str]
    tables_referenced: List[str]


class GovernanceGuardrails:
    """Enforces AST-level safety rules, role table allowlists, and prompt-injection defense."""

    ROLE_TABLE_ALLOWLIST: Dict[str, Set[str]] = {
        "analyst": {
            "dim_product",
            "dim_store",
            "dim_customer",
            "dim_date",
            "dim_region",
            "fact_sales",
            "fact_returns",
            "fact_support_claims",
            "fact_marketing_spend",
        },
        "finance": {
            "dim_product",
            "dim_store",
            "dim_customer",
            "dim_date",
            "dim_region",
            "fact_sales",
            "fact_returns",
            "fact_support_claims",
            "fact_marketing_spend",
            "fact_finance_revenue",
        },
        "admin": {
            "dim_product",
            "dim_store",
            "dim_customer",
            "dim_date",
            "dim_region",
            "fact_sales",
            "fact_returns",
            "fact_support_claims",
            "fact_marketing_spend",
            "fact_finance_revenue",
            "audit_log",
        },
    }

    ROLE_DEFAULT_LIMITS: Dict[str, int] = {
        "analyst": 1000,
        "finance": 5000,
        "admin": 10000,
    }

    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"disregard\s+(?:all\s+)?guidelines",
        r"system\s*prompt\s*:",
        r"\bdrop\s+table\b",
        r"\bdelete\s+from\b",
        r"\btruncate\s+table\b",
        r"\binsert\s+into\b",
        r"\bupdate\s+\w+\s+set\b",
        r"--\s*drop",
        r";\s*drop",
    ]

    def check_prompt_injection(self, text: str) -> Tuple[bool, Optional[str]]:
        """Detect adversarial jailbreak or prompt-injection attempts in user or ticket inputs."""
        t_lower = text.lower()
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, t_lower):
                return True, f"Adversarial prompt injection pattern detected: '{pattern}'"
        return False, None

    def validate_sql(
        self,
        raw_sql: str,
        user_role: str = "analyst",
    ) -> GuardrailResult:
        """Parse SQL with sqlglot, verify read-only AST, role table allowlist, and auto-inject LIMIT."""
        clean_sql = raw_sql.strip().rstrip(";")
        violations: List[str] = []

        # Parse AST using DuckDB dialect
        try:
            parsed = sqlglot.parse_one(clean_sql, read="duckdb")
        except Exception as e:
            return GuardrailResult(
                is_safe=False,
                sanitized_sql=clean_sql,
                decision="BLOCKED_UNSAFE_AST",
                violations=[f"SQL Syntax Error: {e}"],
                tables_referenced=[],
            )

        # 1. Enforce SELECT / WITH Only (Allowlist verification)
        if not isinstance(parsed, (exp.Select, exp.Union)):
            violations.append(f"Disallowed root expression type: {parsed.key}. Only SELECT queries are permitted.")

        # Traverse AST and check for forbidden statements or expressions
        forbidden_expressions = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Create,
            exp.Alter,
            exp.Command,  # PRAGMA, COPY, ATTACH
        )
        for node in parsed.walk():
            if isinstance(node, forbidden_expressions):
                violations.append(f"Forbidden mutation or DDL operation detected: {node.key}")

        # Check for unauthorized file reads (e.g. read_parquet outside marts)
        for node in parsed.find_all((exp.Anonymous, exp.Func)):
            func_name = getattr(node, "name", "").lower() or node.key.lower()
            if func_name in ("read_parquet", "read_csv", "read_json"):
                violations.append(f"Direct file read function '{func_name}' is forbidden; query registered views only.")

        # Defense-in-depth regex check for direct file read primitives
        if re.search(r"\bread_(?:parquet|csv|json)\b", clean_sql, re.IGNORECASE):
            if not any("Direct file read" in v for v in violations):
                violations.append("Direct file read function 'read_parquet' is forbidden; query registered views only.")

        # 2. Extract and Validate Referenced Tables against Role Allowlist
        allowed_tables = self.ROLE_TABLE_ALLOWLIST.get(user_role, self.ROLE_TABLE_ALLOWLIST["analyst"])
        tables_found: Set[str] = set()

        for table in parsed.find_all(exp.Table):
            t_name = table.name.lower()
            # Ignore subqueries or CTE aliases defined in WITH clause
            tables_found.add(t_name)

        # Extract CTE aliases
        cte_aliases: Set[str] = set()
        with_clause = parsed.args.get("with")
        if with_clause:
            for cte in with_clause.expressions:
                cte_aliases.add(cte.alias_or_name.lower())

        real_tables = tables_found - cte_aliases
        for t in real_tables:
            if t not in allowed_tables:
                violations.append(f"Table '{t}' is unauthorized for role '{user_role}'.")

        if violations:
            decision = (
                "BLOCKED_UNAUTHORIZED_TABLE"
                if any("unauthorized" in v for v in violations)
                else "BLOCKED_UNSAFE_AST"
            )
            return GuardrailResult(
                is_safe=False,
                sanitized_sql=clean_sql,
                decision=decision,
                violations=violations,
                tables_referenced=list(real_tables),
            )

        # 3. Enforce Automatic LIMIT cap
        max_limit = self.ROLE_DEFAULT_LIMITS.get(user_role, 1000)
        limit_clause = parsed.args.get("limit")
        mutated = False

        if limit_clause is None:
            parsed = parsed.limit(max_limit)
            mutated = True
        else:
            try:
                current_limit = int(limit_clause.expression.this)
                if current_limit > max_limit:
                    parsed = parsed.limit(max_limit)
                    mutated = True
            except Exception:
                parsed = parsed.limit(max_limit)
                mutated = True

        sanitized_sql = parsed.sql(dialect="duckdb")
        decision = "MUTATED_LIMIT" if mutated else "ALLOWED"

        return GuardrailResult(
            is_safe=True,
            sanitized_sql=sanitized_sql,
            decision=decision,
            violations=[],
            tables_referenced=list(real_tables),
        )
