# OrchardIQ Engineering Task List

This checkable task list maps directly to requirements in `specs/requirements.md` and design specifications in `specs/design.md`.

---

## Phase 1: Repo Scaffold, Synthetic Data & Warehouse Lakehouse
- [x] **TASK-1.1**: Initialize repo configuration (`pyproject.toml`, `.env.example`, `.gitignore`, `config.py`). *[REQ-NL-01]*
- [x] **TASK-1.2**: Implement Kimball-style star schema models and PyArrow schemas (`schema.py`). *[REQ-NL-01]*
- [x] **TASK-1.3**: Implement high-performance synthetic data generator with deterministic seed and partition writer (`generator.py`). *[REQ-NL-01]*
- [x] **TASK-1.4**: Author 31 enterprise knowledge base markdown documents and support ticket generator (`unstructured.py`). *[REQ-RAG-01]*
- [x] **TASK-1.5**: Define the 4 ground-truth injected business stories and verification SQL queries (`stories.py`). *[REQ-NL-02]*
- [x] **TASK-1.6**: Implement DuckDB lakehouse connection, catalog views over partitioned Parquet, and safe query engine (`src/warehouse/`). *[REQ-SQL-01]*
- [x] **TASK-1.7**: Author ADRs (ADR 0001, ADR 0002, ADR 0003) and test suite with 17 passing tests. *[REQ-NL-01]*

---

## Phase 2: Catalog & Hybrid RAG Subsystem
- [x] **TASK-2.1**: Implement VectorStore interface and ChromaDB provider supporting collection creation, metadata filtering, and persistent storage (`src/rag/vector_store.py`). *[REQ-RAG-01]*
- [x] **TASK-2.2**: Implement document parsing, chunking, and metadata tagging for 31 knowledge base Markdown docs and support tickets (`src/rag/indexer.py`). *[REQ-RAG-01]*
- [x] **TASK-2.3**: Implement Hybrid Retriever combining ChromaDB dense vector search with BM25 sparse keyword search and reciprocal rank fusion (`src/rag/retriever.py`). *[REQ-RAG-02]*
- [x] **TASK-2.4**: Implement structured citation generator attributing source documents, titles, and excerpt line ranges (`src/rag/citations.py`). *[REQ-RAG-03]*
- [x] **TASK-2.5**: Build automated RAG retrieval evaluation harness testing Hit-Rate@k and precision on a golden retrieval query set (`tests/test_rag.py`). *[REQ-RAG-04]*
- [x] **TASK-2.6**: Create GitHub Actions CI workflow (`.github/workflows/ci.yml`) running lint, type checks, and pytest on push/PR. *[REQ-API-01]*

---

## Phase 3: SQL Agent & Dual-Sided Governance Agent
- [x] **TASK-3.1**: Build LLM provider abstraction supporting Anthropic Claude (via API key) and offline deterministic MockLLM (`src/agents/llm_provider.py`). *[REQ-SQL-01]*
- [x] **TASK-3.2**: Implement schema-grounded SQL Agent prompting with DuckDB dialect rules, date arithmetic, and schema context (`src/agents/sql_agent.py`). *[REQ-SQL-01]*
- [x] **TASK-3.3**: Implement autonomous self-correction loop in SQL Agent (up to 3 retries on syntax/runtime errors) (`src/agents/sql_agent.py`). *[REQ-SQL-03]*
- [x] **TASK-3.4**: Implement Pre-Execution Governance Agent with `sqlglot` AST validation enforcing SELECT-only allowlist and blocking mutations/DDL (`src/governance/guardrails.py`). *[REQ-GOV-01]*
- [x] **TASK-3.5**: Implement adversarial prompt injection shield blocking hostile prompts and malicious support ticket inputs (`src/governance/guardrails.py`). *[REQ-GOV-02]*
- [x] **TASK-3.6**: Implement Post-Execution Governance Agent enforcing Role-Based Column Masking (SHA-256 tokens for analyst PII) and row-count limits (`src/governance/masking.py`). *[REQ-GOV-03, REQ-GOV-04, REQ-GOV-05]*
- [x] **TASK-3.7**: Implement persistent immutable Audit Log table tracking all query decisions, roles, and safety events (`src/governance/audit.py`). *[REQ-GOV-05]*

---

## Phase 4: Analyst Agent & Statistical ML Tools
- [x] **TASK-4.1**: Implement statistical calculation tools for Period-over-Period (PoP) variance, contribution analysis, and metric lifts (`src/ml/stats.py`). *[REQ-ML-01]*
- [x] **TASK-4.2**: Implement PyTorch weekly demand forecaster (LSTM/MLP architecture) with training/evaluation pipelines and MAPE metrics (`src/ml/forecast.py`). *[REQ-ML-02]*
- [x] **TASK-4.3**: Implement scikit-learn `IsolationForest` time-series anomaly detection tool for claims and return spikes (`src/ml/anomaly.py`). *[REQ-ML-03]*
- [x] **TASK-4.4**: Implement versioned model registry saving trained model weights and metadata in `models/registry/` (`src/ml/registry.py`). *[REQ-ML-04]*
- [x] **TASK-4.5**: Implement Analyst Agent tool wrappers exposing statistical, forecasting, and anomaly tools to LangGraph agents (`src/agents/analyst_agent.py`). *[REQ-ML-01, REQ-ML-02, REQ-ML-03]*
- [x] **TASK-4.6**: Write comprehensive test suite for statistical calculations, ML models, and model registry (`tests/test_ml.py`). *[REQ-ML-01, REQ-ML-02, REQ-ML-03]*

---

## Phase 5: LangGraph Multi-Agent Orchestration & FastAPI
- [x] **TASK-5.1**: Define typed `AgentState` schema and multi-agent graph with Router/Planner, RAG, SQL, Governance, Analyst, and Narrator (`src/agents/graph.py`). *[REQ-AGENT-01]*
- [x] **TASK-5.2**: Implement Narrator Agent synthesizing plain-English executive summaries and declarative Recharts JSON specifications (`src/agents/narrator_agent.py`). *[REQ-NL-01, REQ-NL-03]*
- [x] **TASK-5.3**: Implement short-term session conversation memory and long-term saved insight storage (`src/agents/memory.py`). *[REQ-AGENT-03]*
- [x] **TASK-5.4**: Implement FastAPI application router with JWT / API-key authentication supporting 3 roles (`src/api/auth.py`, `src/api/main.py`). *[REQ-API-01]*
- [x] **TASK-5.5**: Implement streaming SSE endpoint (`POST /ask`) broadcasting agent reasoning steps in real-time (`src/api/routes/ask.py`). *[REQ-AGENT-02]*
- [x] **TASK-5.6**: Implement REST endpoints: `/sessions/{id}`, `/trace/{run_id}`, `/catalog/search`, `/forecast`, `/quality/report`, `/audit`, `/health`, `/metrics` (`src/api/routes/`). *[REQ-API-01]*
- [x] **TASK-5.7**: Write end-to-end integration test suite verifying that all 4 injected stories are answered correctly through the agent graph (`tests/test_agents_e2e.py`). *[REQ-NL-02]*

---

## Phase 6: Modern Web Application Workspace (Next.js 15)
- [x] **TASK-6.1**: Scaffold Next.js 15 application with TypeScript, Tailwind CSS, and Recharts in `frontend/`. *[REQ-UI-01]*
- [x] **TASK-6.2**: Implement custom design system tokens, dark/light mode toggle, typography, and responsive navigation shell (`frontend/src/`). *[REQ-UI-01]*
- [x] **TASK-6.3**: Implement Chat Workspace with streaming agent-step timeline, markdown narrative renderer, Recharts visualizer, SQL viewer, citations, and governance badges (`frontend/src/components/`). *[REQ-UI-01, REQ-UI-03]*
- [x] **TASK-6.4**: Implement live Role Switcher (`analyst`, `finance`, `admin`) demonstrating immediate PII masking in query outputs (`frontend/src/components/Header.tsx`). *[REQ-UI-02]*
- [x] **TASK-6.5**: Implement clickable Demo Question chips for the 4 injected business stories with immediate zero-setup execution (`frontend/src/components/DemoChips.tsx`). *[REQ-UI-03]*
- [x] **TASK-6.6**: Build dedicated pages: Data Catalog Browser, Eval Results Dashboard, Data Quality Monitor, Audit Log, and Live Stream Tile (`frontend/src/components/`). *[REQ-UI-01]*
- [x] **TASK-6.7**: Write Playwright end-to-end smoke tests capturing screenshots and verifying live UI interactions (`frontend/tests/smoke.spec.ts`). *[REQ-UI-01, REQ-UI-03]*

---

## Phase 7: Evals, Observability & Data Pipelines
- [x] **TASK-7.1**: Construct golden evaluation benchmark set of 40+ enterprise business questions with ground truth SQL and expected facts (`evals/golden_set.json`). *[REQ-API-04]*
- [x] **TASK-7.2**: Implement evaluation runner measuring SQL execution accuracy, answer correctness, guardrail pass rate, and p50/p95 latency (`evals/runner.py`). *[REQ-API-04]*
- [x] **TASK-7.3**: Implement OpenTelemetry-style structured tracing and Prometheus `/metrics` exporter (`src/observability/`). *[REQ-API-02, REQ-API-03]*
- [x] **TASK-7.4**: Implement Data Quality validation engine checking freshness, null rates, and row-count drift on the lakehouse (`src/pipelines/quality.py`). *[REQ-API-01]*
- [x] **TASK-7.5**: Implement batch ETL orchestration pipeline (`raw -> staging -> marts`) with automated DQ gates (`src/pipelines/etl.py`). *[REQ-API-01]*
- [x] **TASK-7.6**: Implement simulated near-real-time event streaming pipeline feeding live transactions to the UI tile (`src/pipelines/stream.py`). *[REQ-UI-01]*

---

## Phase 8: Docker, AWS Deploy Skeleton, Docs & Release
- [x] **TASK-8.1**: Create production multi-stage Dockerfile for FastAPI backend and Next.js frontend (`Dockerfile`, `Dockerfile.frontend`). *[REQ-NL-01]*
- [x] **TASK-8.2**: Create `docker-compose.yml` for unified single-command deployment with demo mode enabled. *[REQ-NL-01]*
- [x] **TASK-8.3**: Author Terraform / AWS CDK infrastructure skeleton for ECS/App Runner, S3 Lakehouse, and CloudWatch alarms (`infra/`). *[REQ-API-01]*
- [x] **TASK-8.4**: Implement DEMO_MODE toggle with cached fallback responses and per-IP rate limiting for public showcase. *[REQ-NL-01]*
- [x] **TASK-8.5**: Author comprehensive `README.md` with Mermaid diagrams, eval benchmark table, governance model, and "What I Would Do at Apple Scale" architecture section. *[REQ-NL-01]*
- [x] **TASK-8.6**: Deploy backend and frontend to public hosting and verify live URL using Playwright. *[REQ-UI-01]*
- [x] **TASK-8.7**: Tag release `v0.1.0` and update repo metadata. *[REQ-NL-01]*
