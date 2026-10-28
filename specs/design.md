# OrchardIQ Technical Architecture & System Design

## 1. System Overview & Component Diagram

OrchardIQ couples an in-process vectorized analytical lakehouse (DuckDB over partitioned Parquet) with an enterprise knowledge vector store (ChromaDB) orchestrated by a multi-agent state graph (LangGraph) and served via FastAPI and Next.js 15.

```mermaid
graph TB
    subgraph Client ["Frontend Layer (Next.js 15 + TypeScript + Tailwind + Recharts)"]
        UI_CHAT["Chat Workspace (SSE Timeline)"]
        UI_CATALOG["Catalog Browser"]
        UI_EVAL["Eval Results Dashboard"]
        UI_DQ["Data Quality Monitor"]
        UI_AUDIT["Governance Audit Log"]
        UI_STREAM["Live Event Stream Tile"]
    end

    subgraph API ["FastAPI Application Gateway"]
        AUTH["Role Authenticator (Analyst / Finance / Admin)"]
        ROUTER_API["FastAPI REST & SSE Router"]
        TRACER["Structured OpenTelemetry Tracer"]
        METRICS["Prometheus Metrics Registry (/metrics)"]
    end

    subgraph Orchestration ["LangGraph Multi-Agent Orchestrator"]
        PLANNER["Router / Planner Agent"]
        RAG["Catalog / RAG Agent"]
        SQL_AGENT["SQL Agent (Self-Correction Loop)"]
        GOV["Governance Agent (Pre/Post AST & RBAC)"]
        ANALYST["Analyst Agent (PoP & Driver Analysis)"]
        NARRATOR["Narrator Agent (Executive Synthesis & Recharts)"]
    end

    subgraph Intelligence ["Machine Learning & Analytical Tools"]
        TORCH["PyTorch Weekly Demand Forecaster (LSTM/MLP)"]
        SKLEARN["scikit-learn IsolationForest (Anomaly Detector)"]
        REGISTRY["Versioned Model Registry"]
    end

    subgraph Storage ["Data Platform & Lakehouse Layer"]
        DUCK["DuckDB In-Process Vectorized OLAP Engine"]
        PARQUET[("Hive-Partitioned Parquet Marts (~2.1M Rows)")]
        CHROMA[("ChromaDB Vector Store (Hybrid BM25 + Dense)")]
        AUDIT_DB[("DuckDB Audit & Trace Storage")]
    end

    Client -->|HTTP / SSE| API
    API --> AUTH
    AUTH --> ROUTER_API
    ROUTER_API --> PLANNER
    PLANNER --> RAG
    RAG --> CHROMA
    RAG --> SQL_AGENT
    SQL_AGENT --> GOV
    GOV --> DUCK
    DUCK --> PARQUET
    DUCK --> ANALYST
    ANALYST --> TORCH
    ANALYST --> SKLEARN
    ANALYST --> NARRATOR
    GOV --> AUDIT_DB
    ROUTER_API --> TRACER
    TRACER --> METRICS
```

---

## 2. LangGraph Multi-Agent Graph Architecture

The multi-agent workflow is implemented as an explicit LangGraph state machine rather than an unstructured monolithic chain. Each node mutates a strictly typed `AgentState` object.

```mermaid
stateDiagram-v2
    [*] --> RouterPlanner
    
    RouterPlanner --> CatalogRAG: Intent = data_query | report | anomaly
    RouterPlanner --> Narrator: Intent = general_glossary
    
    CatalogRAG --> SQLAgent: Schema & Context Grounded
    
    SQLAgent --> GovernancePreCheck: SQL Generated
    
    GovernancePreCheck --> SQLAgent: Rejected / Unsafe AST (Self-Correct)
    GovernancePreCheck --> DuckDBExecution: Allowed (SELECT Only)
    
    DuckDBExecution --> SQLAgent: Execution Error (Attempt < 3)
    DuckDBExecution --> GovernancePostCheck: Execution Succeeded
    
    GovernancePostCheck --> AnalystAgent: Masked Data & Safe Results
    
    AnalystAgent --> MachineLearningTools: Anomaly or Forecast Required
    MachineLearningTools --> AnalystAgent: Metrics & Forecast Results
    
    AnalystAgent --> Narrator: Statistical Synthesis Ready
    
    Narrator --> [*]: Emits Executive Summary, Chart Spec & Badges
```

### State Schema (`AgentState`)
```python
class AgentState(TypedDict):
    session_id: str
    run_id: str
    question: str
    user_role: str  # analyst, finance, admin
    intent: str     # data_query, definition, forecast, anomaly, report
    plan_steps: List[str]
    citations: List[Dict[str, Any]]
    retrieved_context: str
    sql_query: Optional[str]
    sql_attempts: List[Dict[str, Any]]
    raw_results: Optional[List[Dict[str, Any]]]
    masked_results: Optional[List[Dict[str, Any]]]
    statistical_findings: Optional[Dict[str, Any]]
    ml_output: Optional[Dict[str, Any]]
    governance_decision: Dict[str, Any]
    narrative: Optional[str]
    chart_spec: Optional[Dict[str, Any]]
    follow_up_questions: List[str]
    trace_events: List[Dict[str, Any]]
```

---

## 3. Sequence Diagram for `POST /ask` (SSE Streaming)

```mermaid
sequenceDiagram
    autonumber
    actor User as Client (Next.js)
    participant API as FastAPI Router
    participant Planner as Router/Planner
    participant RAG as Catalog/RAG Agent
    participant SQL as SQL Agent
    participant Gov as Governance Agent
    participant Lakehouse as DuckDB Engine
    participant Analyst as Analyst Agent
    participant Narrator as Narrator Agent

    User->>API: POST /ask {question, session_id, role}
    API-->>User: 200 OK (Content-Type: text/event-stream)
    
    API->>Planner: Initialize Run & Classify Intent
    Planner-->>User: event: step {name: "Planner", status: "Planning decomposition..."}
    
    Planner->>RAG: Retrieve Schemas & Postmortems
    RAG-->>User: event: step {name: "CatalogRAG", status: "Retrieved 4 citations"}
    
    RAG->>SQL: Generate Text-to-SQL
    SQL->>Gov: Pre-execution AST Validation
    Gov-->>User: event: step {name: "Governance", status: "AST Validated: SELECT Only, Role: analyst"}
    
    Gov->>Lakehouse: Execute SQL Query
    Lakehouse-->>Gov: Result Set (145ms)
    
    Gov->>Gov: Apply Role Column Masking (SHA-256 PII)
    Gov->>Lakehouse: Insert Record into audit_log
    
    Gov->>Analyst: Forward Safe Masked Data
    Analyst-->>User: event: step {name: "Analyst", status: "Running PoP & Outlier Detection"}
    
    Analyst->>Narrator: Forward Statistical Synthesis
    Narrator->>Narrator: Synthesize Executive Narrative & Recharts JSON
    Narrator-->>User: event: answer {narrative, chart_spec, sql, citations, badges}
    Narrator-->>User: event: done
```

---

## 4. API Contracts & Endpoints

| Method | Endpoint | Description | Request Body / Query | Response Model |
|---|---|---|---|---|
| `POST` | `/ask` | Streaming multi-agent query endpoint | `AskRequest` (`question`, `session_id`, `role`, `include_trace`) | Server-Sent Events (`event: step`, `event: answer`, `event: done`) |
| `GET` | `/sessions/{id}` | Retrieve session history and saved insights | Path: `id` | `SessionHistoryResponse` |
| `GET` | `/trace/{run_id}` | Retrieve execution trace and latency | Path: `run_id` | `TraceResponse` (steps, latency, tokens, cost) |
| `GET` | `/catalog/search` | Semantic and keyword catalog search | Query: `q`, `category`, `limit` | `CatalogSearchResponse` (tables, metrics, postmortems) |
| `POST` | `/forecast` | Run PyTorch weekly demand forecaster | `ForecastRequest` (`product_id`, `weeks_ahead`, `horizon`) | `ForecastResponse` (projected units, MAPE, confidence bounds) |
| `GET` | `/quality/report` | Lakehouse Data Quality health report | None | `DataQualityReport` (freshness, null rates, drift) |
| `GET` | `/audit` | Retrieve governance audit log entries | Query: `limit`, `role`, `flagged_only` | `AuditLogResponse` (queries, roles, decisions, timestamps) |
| `GET` | `/health` | System readiness and lakehouse status | None | `HealthResponse` (`status: ok`, `duckdb: ok`, `chroma: ok`) |
| `GET` | `/metrics` | Prometheus format platform metrics | None | Text (`text/plain; version=0.0.4`) |

---

## 5. Security & Governance Architecture (RBAC & Defense-in-Depth)

```mermaid
flowchart TD
    Q[Incoming SQL Candidate] --> AST[sqlglot AST Parser]
    
    subgraph PreExecution ["Pre-Execution Guardrails"]
        AST --> V1{Is Statement SELECT / WITH Only?}
        V1 -- No --> B1[REJECT: Mutation / DDL Forbidden]
        V1 -- Yes --> V2{Contains Cross-DB File Reads?}
        V2 -- Yes --> B2[REJECT: File System Read Prohibited]
        V2 -- No --> V3{Role Table Allowlist Check}
        V3 -- Violation --> B3[REJECT: Unauthorized Table Access]
        V3 -- Passed --> EX[Execute in DuckDB with Timeout & Row Cap]
    end

    subgraph PostExecution ["Post-Execution Guardrails"]
        EX --> R[Raw Result Set]
        R --> ROLE{User Role}
        ROLE -- analyst --> MASK[Mask PII Columns with SHA-256 / ***MASKED***]
        ROLE -- finance --> FIN_MASK[Mask PII; Permit GAAP Financial Ledgers]
        ROLE -- admin --> UNMASK[Permit Unmasked Data]
        MASK & FIN_MASK & UNMASK --> AUDIT[Write Transaction to audit_log]
    end

    AUDIT --> OUT[Sanitized Response to Analyst Agent]
```

### Role-Based Access Matrix

| Role | Allowed Tables | PII Masking (`dim_customer`) | Row Limit | Finance Reconciliation Access |
|---|---|---|---|---|
| `analyst` | `fact_sales`, `fact_returns`, `fact_support_claims`, `fact_marketing_spend`, `dim_*` | **Masked** (`email`, `phone`, `first_name`, `last_name`, `address`) | 1,000 rows | Aggregated only |
| `finance` | All tables including `fact_finance_revenue` | **Masked** | 5,000 rows | **Full GAAP & Deferred Ledgers** |
| `admin` | All tables | **Unmasked** (Audited) | 10,000 rows | Full Access |

---

## 6. Failure Modes & Autonomous Self-Healing

| Failure Scenario | Detection Mechanism | Self-Healing / Mitigation Strategy |
|---|---|---|
| **SQL Syntax / Runtime Error** | DuckDB exception caught in `SQLAgent` | Autonomous self-correction loop (up to 3 retries) sending error context back to LLM. |
| **Prompt Injection Attack** | AST validation & regex prompt shield | SQL blocked immediately; security warning injected; security incident recorded in `audit_log`. |
| **Query Timeout (>30s)** | DuckDB execution thread timeout | Query terminated; agent notified; plan decomposed into smaller partitioned intervals. |
| **LLM Provider API Outage** | Anthropic API connection timeout or rate limit | Fallback to deterministic `MockLLM` with cached golden-response repository (ensuring live demo never fails). |
| **Vector Store Cold Start** | ChromaDB collection missing | Automated on-demand indexing job triggered from `docs/knowledge_base/` and `data/unstructured/`. |
