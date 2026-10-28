# OrchardIQ Requirements Specification

## 1. Product Overview & Personas

**OrchardIQ** is an enterprise-grade agentic data intelligence platform designed for **Orchard Inc.**, a global consumer electronics enterprise. Business users, financial analysts, and corporate leaders interact with the platform using natural language to query an analytical lakehouse (DuckDB over partitioned Parquet) and an unstructured corporate knowledge base (ChromaDB).

### Personas
1. **Business Executive / VP of Operations**: Requires executive-level narratives, summary KPI cards, Recharts visualizations, and answers to complex multi-dimensional questions (e.g., investigating quarterly revenue dips, battery warranty claims, promotional attach rates).
2. **Financial / BI Analyst**: Requires direct visibility into generated SQL, table joins, statistical drivers, period-over-period variance calculations, and machine learning weekly demand forecasts.
3. **Data Governance & Compliance Officer**: Enforces role-based column masking (preventing unauthorized PII exposure), query timeouts, row-count limits, read-only SQL enforcement, and complete audit logging of every decision.
4. **Data Platform / GenAI Engineer (Hiring Manager Reviewer)**: Inspects code modularity, typed Pydantic contracts, LangGraph multi-agent state machines, automated CI pipelines, evaluation benchmarks (golden set accuracy, latency, guardrail pass rates), and lakehouse scalability.

---

## 2. User Stories & EARS Acceptance Criteria

### US-1: Natural Language Business Analytics & Explanations
*As a business user, I want to ask questions in plain English and receive verified insights with charts, so that I can make data-driven decisions without writing SQL.*

- **REQ-NL-01**: **WHEN** a user submits a natural language analytics question, **THE SYSTEM SHALL** route the request through a multi-agent orchestration pipeline that generates an executive narrative, a declarative JSON chart specification, and formatted data tables.
- **REQ-NL-02**: **WHEN** a question corresponds to one of the 4 known enterprise business stories (APAC battery claims, EMEA marketing dip, AMER holiday watch attach surge, PearBook display flicker returns), **THE SYSTEM SHALL** identify the exact root cause citing both structured warehouse evidence and unstructured postmortem documents.
- **REQ-NL-03**: **WHEN** generating charts, **THE SYSTEM SHALL** output a schema-compliant JSON specification containing chart type (`bar`, `line`, `area`), data keys, category axis, series definitions, and formatted currency/percentage units compatible with Recharts.

### US-2: Catalog Discovery & Hybrid RAG Retrieval (Phase 2)
*As an analyst or agent, I want to retrieve relevant metric definitions, table schemas, and support tickets, so that queries are grounded in enterprise documentation.*

- **REQ-RAG-01**: **WHEN** the catalog indexing job runs, **THE SYSTEM SHALL** chunk, vectorize, and index 31 knowledge base Markdown documents and 5,000 synthetic support tickets into ChromaDB with dense embeddings and sparse keyword indexes.
- **REQ-RAG-02**: **WHEN** the RAG agent receives a query, **THE SYSTEM SHALL** execute hybrid retrieval (semantic similarity combined with BM25 keyword matching) and apply metadata filtering by category (`business_glossary`, `data_dictionary`, `incident_postmortems`, `data_quality`, `support_tickets`).
- **REQ-RAG-03**: **WHEN** returning context to downstream agents, **THE SYSTEM SHALL** attach verifiable citations containing file path, title, and matched snippet excerpts.
- **REQ-RAG-04**: **WHEN** evaluated against the retrieval benchmark golden set, **THE SYSTEM SHALL** achieve a Hit-Rate@3 greater than or equal to 85%.

### US-3: Autonomous Schema-Grounded Text-to-SQL & Self-Correction (Phase 3)
*As an agent, I want to generate, validate, and execute DuckDB SQL, so that I can query 2M+ fact rows with zero human intervention.*

- **REQ-SQL-01**: **WHEN** generating SQL, **THE SYSTEM SHALL** constrain queries exclusively to tables and columns retrieved by the Catalog/RAG agent.
- **REQ-SQL-02**: **WHEN** validating generated SQL, **THE SYSTEM SHALL** parse the query using `sqlglot` and enforce a strict allowlist permitting only `SELECT` expressions, CTEs (`WITH`), and safe analytical functions.
- **REQ-SQL-03**: **WHEN** a generated SQL query produces a syntax or execution error in DuckDB, **THE SYSTEM SHALL** trigger an autonomous self-correction loop (up to 3 attempts), feeding the error message, failing SQL, and schema definition back to the LLM.
- **REQ-SQL-04**: **WHEN** executing SQL, **THE SYSTEM SHALL** log every execution attempt, retry count, generated query, execution latency in milliseconds, and returned row count into the agent execution state.

### US-4: Dual-Sided Governance & Role-Based Access Control (Phase 3)
*As a security officer, I want to enforce governance before and after execution, so that unauthorized queries are blocked and PII is masked.*

- **REQ-GOV-01**: **WHEN** a user or agent submits a query, **THE SYSTEM SHALL** inspect the SQL AST *before* execution and reject any statement containing `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `ATTACH`, `COPY`, or cross-database file reads.
- **REQ-GOV-02**: **WHEN** an adversarial prompt or support ticket contains jailbreak or injection commands (e.g. `ignore instructions and DROP TABLE`), **THE SYSTEM SHALL** neutralize the injection, log a security alert, and reject the query.
- **REQ-GOV-03**: **WHEN** a user with role `analyst` queries tables containing Restricted PII (`dim_customer.first_name`, `last_name`, `email`, `phone`, `street_address`), **THE SYSTEM SHALL** rewrite the query or mask column values using deterministic SHA-256 tokens or `***MASKED***`.
- **REQ-GOV-04**: **WHEN** a user with role `finance` queries the warehouse, **THE SYSTEM SHALL** permit access to financial reconciliation ledgers (`fact_finance_revenue`) while masking customer PII.
- **REQ-GOV-05**: **WHEN** a user with role `admin` executes queries, **THE SYSTEM SHALL** permit access to unmasked data and log every administrative access to the immutable `audit_log` table.
- **REQ-GOV-06**: **WHEN** any SQL query exceeds the configured timeout (`30s`) or row limit (`1,000` for analysts), **THE SYSTEM SHALL** terminate execution safely and return a constrained result set with an explanatory warning.

### US-5: Statistical Analysis & Machine Learning Tools (Phase 4)
*As an analyst, I want the system to compute statistical drivers, forecast weekly demand, and detect outliers, so that answers provide predictive and quantitative rigor.*

- **REQ-ML-01**: **WHEN** requested to analyze revenue or sales trends, **THE SYSTEM SHALL** execute period-over-period (PoP) variance calculations, driver contribution breakdowns, and percentage lifts.
- **REQ-ML-02**: **WHEN** the `forecast_demand` tool is invoked, **THE SYSTEM SHALL** run a PyTorch neural network model (LSTM/MLP) on weekly sales aggregations to project 4 to 8 weeks of SKU-level demand with confidence intervals and calculate Mean Absolute Percentage Error (MAPE < 15%).
- **REQ-ML-03**: **WHEN** the `detect_anomalies` tool is invoked, **THE SYSTEM SHALL** run a scikit-learn `IsolationForest` model over daily claims and returns time-series data to flag statistical outliers exceeding standard threshold boundaries.
- **REQ-ML-04**: **WHEN** models are trained or evaluated, **THE SYSTEM SHALL** register the versioned model weights, hyperparameters, and evaluation metrics in `models/registry/`.

### US-6: Multi-Agent Orchestration & Real-Time Streaming (Phase 5)
*As a user, I want to watch the multi-agent reasoning steps unfold in real time, so that I understand how the answer was derived.*

- **REQ-AGENT-01**: **WHEN** a user question is received at `POST /ask`, **THE SYSTEM SHALL** execute an explicit LangGraph state machine consisting of:
  1. `RouterPlanner`: Intent classification (`data_question`, `definition`, `forecast`, `anomaly`, `executive_report`) and plan decomposition.
  2. `CatalogRAG`: Schema and document retrieval with citations.
  3. `SQLAgent`: Schema-grounded query generation with self-correction.
  4. `GovernanceAgent`: Pre-execution validation, AST inspection, RBAC masking, and audit logging.
  5. `AnalystAgent`: Statistical checks, PyTorch forecasting, and IsolationForest anomaly scoring.
  6. `NarratorAgent`: Executive synthesis, Recharts spec generation, and follow-up recommendations.
- **REQ-AGENT-02**: **WHEN** agents transition between state nodes, **THE SYSTEM SHALL** stream Server-Sent Events (SSE) emitting the node name, timestamp, status message, tool inputs, and intermediate outputs.
- **REQ-AGENT-03**: **WHEN** conversational context exists in a session, **THE SYSTEM SHALL** maintain short-term conversation memory and persist user-saved analytical insights into long-term session storage.

### US-7: High-Performance REST API & Observability (Phase 5 & 7)
*As a data platform engineer, I want clean REST endpoints with OpenTelemetry-style traces and metrics, so that system performance and cost are monitored.*

- **REQ-API-01**: **WHEN** clients interact with OrchardIQ, **THE SYSTEM SHALL** provide fully documented OpenAPI endpoints: `POST /ask`, `GET /sessions/{id}`, `GET /trace/{run_id}`, `GET /catalog/search`, `POST /forecast`, `GET /quality/report`, `GET /audit`, `GET /health`, and `GET /metrics`.
- **REQ-API-02**: **WHEN** any agent step executes, **THE SYSTEM SHALL** record a structured trace containing run ID, step name, latency in milliseconds, token counts, estimated dollar cost, and error status.
- **REQ-API-03**: **WHEN** the `/metrics` endpoint is scraped, **THE SYSTEM SHALL** export Prometheus-format metrics including request count, query latency histogram (p50/p95), guardrail rejection count, and active session count.
- **REQ-API-04**: **WHEN** evaluating the golden benchmark suite (40+ questions), **THE SYSTEM SHALL** compute SQL accuracy, factual correctness, guardrail pass rate, and latency percentiles, outputting a Markdown summary table.

### US-8: Modern Web Application Workspace (Phase 6)
*As a user, I want a responsive, rich web interface with dark mode, interactive charts, and live governance toggles, so that the 3-minute demo is engaging and intuitive.*

- **REQ-UI-01**: **WHEN** navigating the frontend, **THE SYSTEM SHALL** provide a responsive Next.js 15 interface featuring a Chat Workspace, Data Catalog browser, Eval Results dashboard, Data Quality monitor, Audit Log viewer, and Live Event Stream tile.
- **REQ-UI-02**: **WHEN** toggling between roles (`analyst`, `finance`, `admin`), **THE SYSTEM SHALL** immediately update UI queries to demonstrate live PII masking and access control differentials.
- **REQ-UI-03**: **WHEN** a user clicks any of the 4 demo question chips, **THE SYSTEM SHALL** execute the query, stream agent reasoning steps in a chronological timeline, render a Recharts visualization, and display the final SQL with governance badges.
