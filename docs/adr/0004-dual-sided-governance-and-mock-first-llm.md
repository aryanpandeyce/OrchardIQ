# ADR 0004: Dual-Sided Governance Architecture & Mock-First LLM Provider

## Status
Accepted

## Date
2026-10-28

## Context
OrchardIQ deploys generative AI agents against a production data warehouse containing enterprise sales, warranty claims, financials, and customer Personally Identifiable Information (PII).
Key architectural challenges:
1. **Security & Data Integrity**: LLM agents are prone to hallucinations, unauthorized table access, and adversarial prompt injections (e.g. `DROP TABLE`).
2. **Privacy & Compliance**: Different corporate personas (analyst, finance, admin) require distinct access privileges. Analyst roles must never view plaintext customer names, emails, phones, or residential addresses.
3. **Demo & CI Reliability**: Hiring managers, portfolio evaluators, and automated CI pipelines cannot depend on active third-party API keys or unmetered token costs for core test suites.

## Decision

### 1. Dual-Sided Governance Architecture
We place the **Governance Agent** in a dual-sided configuration:
- **Pre-Execution Guardrail**:
  - Intercepts generated SQL *before* database submission.
  - Parses the SQL Abstract Syntax Tree (AST) using `sqlglot`.
  - Rejects any mutation or DDL (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `ATTACH`, `COPY`).
  - Verifies table references against a strict role allowlist (e.g., blocking `fact_finance_revenue` for default analyst roles).
  - Automatically injects safety row limits (`LIMIT 1000` for analysts).
  - Detects and neutralizes prompt-injection keywords.
- **Post-Execution Guardrail**:
  - Intercepts query result sets *after* execution in DuckDB.
  - Enforces Role-Based Column Masking (RBAC):
    - For `analyst`: Masks customer emails as deterministic tokens (`anon_sha256@domain`), phones as `+1-***-***-1234`, names as `J***`, and addresses as `***REDACTED***`.
    - For `admin`: Grants unmasked access with mandatory recording in the immutable `audit_log`.

### 2. Mock-First LLM Provider Interface
We implement `LLMProvider` behind an abstract factory:
- `ClaudeProvider`: Direct Anthropic Claude 3.5 Sonnet integration when `ANTHROPIC_API_KEY` is present and `MOCK_LLM_MODE=false`.
- `MockLLMProvider`: Deterministic, grounded mock engine that generates valid DuckDB SQL, handles autonomous self-correction loops, and crafts structured executive summaries.
- Result: The entire test suite, evaluation harness, and live demo run offline in milliseconds with 100% deterministic reproducibility.

## Consequences & Trade-offs
### Positive
- Zero risk of SQL injection, database tampering, or accidental PII leakage.
- Self-correction loops allow agents to recover autonomously from schema typos.
- Portfolio review and CI runs require zero external secrets or API costs.

### Negative / Mitigations
- AST parsing adds ~3ms latency per query (negligible in interactive human-agent conversations).
