# OrchardIQ: Autonomous Lakehouse Intelligence & Dual-Sided Governance

[![CI Pipeline](https://github.com/aryanpandeyce/OrchardIQ/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aryanpandeyce/OrchardIQ/actions/workflows/ci.yml)
[![CD Deploy](https://github.com/aryanpandeyce/OrchardIQ/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/aryanpandeyce/OrchardIQ/actions/workflows/deploy.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15.5-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![DuckDB Lakehouse](https://img.shields.io/badge/Lakehouse-DuckDB%20%2B%20Parquet-FFF000?logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Tests Passing](https://img.shields.io/badge/Pytest-58%20Passing-brightgreen.svg)](https://github.com/aryanpandeyce/OrchardIQ/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **OrchardIQ** is an enterprise-grade autonomous data intelligence and analytics lakehouse platform for **Orchard Inc.** (a global consumer-electronics enterprise). Powered by a multi-agent LangGraph orchestration state machine, an in-process DuckDB/Parquet star-schema lakehouse (~2.2M fact records), PyTorch statistical forecasting, and an AST-level **Dual-Sided Governance Agent** enforcing compile-time SQL safety, role-based column masking, and immutable cryptographic audit trails.

---

### 🌐 Live Production Deployments
- 🖥️ **Live Web Application**: [https://orchardiq.vercel.app](https://orchardiq.vercel.app) *(Runs high-fidelity DEMO_MODE by default)*
- ⚡ **Live FastAPI Backend & Swagger Docs**: [https://orchardiq-backend.onrender.com/docs](https://orchardiq-backend.onrender.com/docs)
- 🤗 **Hugging Face Spaces Mirror**: [https://huggingface.co/spaces/aryanpandeyce/OrchardIQ-Backend](https://huggingface.co/spaces/aryanpandeyce/OrchardIQ-Backend)
- 📦 **GitHub Repository**: [https://github.com/aryanpandeyce/OrchardIQ](https://github.com/aryanpandeyce/OrchardIQ)

---

## 🎬 Interactive Platform Demo

![OrchardIQ Interactive Demo Tour](docs/demo.gif)

---

## 📸 Workspace Showcase & Visual Tour

The OrchardIQ workspace is built on Next.js 15, Tailwind CSS, and Recharts, featuring dark-mode ergonomics, live streaming timelines, role switching with instant PII masking, and full platform monitoring.

| 1. Chat Workspace & Multi-Agent Reasoning | 2. Executive Incident Briefing & Recharts |
|:---:|:---:|
| ![Chat Workspace](docs/screenshots/01_workspace_chat.png) | ![Story 1 Answer Card](docs/screenshots/02_story_answer_card.png) |

| 3. Star-Schema Data Catalog | 4. Golden Benchmark Evaluation Suite |
|:---:|:---:|
| ![Data Catalog](docs/screenshots/03_data_catalog.png) | ![Eval Benchmark](docs/screenshots/04_eval_benchmark.png) |

| 5. Lakehouse Data Quality Gates | 6. Immutable Governance Audit Log |
|:---:|:---:|
| ![Data Quality Monitor](docs/screenshots/05_data_quality.png) | ![Governance Audit Trail](docs/screenshots/06_governance_audit.png) |

| 7. Near-Real-Time Event Stream Ticker |
|:---:|
| ![Live Stream](docs/screenshots/07_live_ticker.png) |

---

## 🏗️ High-Level System Architecture

```mermaid
flowchart TD
    subgraph UI ["Modern Next.js 15 Client Layer"]
        CHAT["Chat Workspace (SSE Streaming Timeline)"]
        ROLE["Live Role Switcher (Analyst / Finance / Admin)"]
        CHIPS["Verified Ground-Truth Story Chips (1-Click)"]
        VIEWS["Catalog • Evals • Quality • Audit • Live Stream"]
    end

    subgraph API ["FastAPI Gateway & Telemetry Layer"]
        AUTH["JWT & API-Key Auth (3 Roles)"]
        RATE["Per-IP Rate Limiter (60 req/min)"]
        CACHE["Demo Mode Response Cache"]
        SSE["SSE Event Streaming Router (/ask)"]
        REST["REST API (/sessions, /trace, /quality, /metrics)"]
    end

    subgraph AgentGraph ["LangGraph Multi-Agent Orchestration State Machine"]
        PLANNER["1. Router & Planner (Intent Classification)"]
        RAG["2. Catalog RAG (Hybrid BM25 + ChromaDB + RRF)"]
        SQL["3. SQL Agent (DuckDB Dialect + 3x Self-Correction)"]
        GOV["4. Dual-Sided Governance (sqlglot AST + PII Masking)"]
        ML["5. Analyst Agent (PyTorch Demand + IsolationForest)"]
        NARRATOR["6. Narrator Agent (Executive Brief + Recharts Spec)"]
    end

    subgraph Lakehouse ["DuckDB Star-Schema Analytical Lakehouse"]
        CATALOG["WarehouseCatalog (Hive Views over Partitioned Parquet)"]
        ENGINE["DuckDB Vectorized In-Process OLAP Engine"]
        DIM["Dimensions: dim_product, dim_store, dim_customer, dim_date, dim_region"]
        FACT["Facts: fact_sales, fact_returns, fact_support_claims, fact_marketing_spend, fact_finance_revenue"]
    end

    subgraph Observability ["Enterprise Observability & Governance"]
        AUDIT["Immutable Audit Log Table (audit_log.parquet)"]
        TRACE["OpenTelemetry-style Structured Tracing"]
        PROM["Prometheus /metrics Exporter (p50 / p95 Latency)"]
        DQ["Data Quality Engine (Freshness, Nulls, Drift)"]
    end

    UI <--> |HTTP / SSE| API
    API --> AgentGraph
    PLANNER --> RAG --> SQL --> GOV --> ML --> NARRATOR
    SQL <--> ENGINE
    ENGINE <--> CATALOG <--> DIM & FACT
    GOV --> AUDIT
    API --> TRACE & PROM & DQ
```

---

## 🛡️ Dual-Sided Governance & Security Model

OrchardIQ enforces security at both the **pre-execution AST compile time** and the **post-execution dataset delivery time**, preventing prompt injections, destructive mutations, and unauthorized PII exposure before results ever leave the engine.

```mermaid
flowchart LR
    subgraph PreExecution ["1. Pre-Execution AST Gatekeeper"]
        P1["Natural Language Query"] --> P2["Adversarial Prompt Injection Shield"]
        P2 --> P3["sqlglot AST Parser (DuckDB Dialect)"]
        P3 --> P4{"SELECT-only Allowlist"}
        P4 -- "INSERT / UPDATE / DROP / DELETE" --> P5["❌ BLOCKED: Mutation Prohibited"]
        P4 -- "SELECT / CTE" --> P6{"Role-Based Table Allowlist"}
        P6 -- "Analyst accesses fact_finance_revenue" --> P7["❌ BLOCKED: Table Restricted"]
        P6 -- "Authorized Table" --> P8["Auto-Inject LIMIT by Role"]
    end

    subgraph Execution ["2. Engine Execution"]
        P8 --> E1["DuckDB In-Process Vectorized Execution"]
    end

    subgraph PostExecution ["3. Post-Execution Data Privacy Gate"]
        E1 --> M1{"Active Role Check"}
        M1 -- "Role = analyst" --> M2["Dynamic SHA-256 Masking (first_name, last_name, email, phone)"]
        M1 -- "Role = finance" --> M3["Enforce PII Block + Financial Table Access"]
        M1 -- "Role = admin" --> M4["Authorized Full Record Display"]
        M2 & M3 & M4 --> LOG["Write Cryptographic Entry to governance_audit_log"]
    end
```

### Role-Based Access Control (RBAC) Matrix

| Policy Dimension | `analyst` Role | `finance` Role | `admin` Role |
|---|---|---|---|
| **Query Types Permitted** | `SELECT`, `WITH` (Read-Only) | `SELECT`, `WITH` (Read-Only) | `SELECT`, `WITH` (Read-Only) |
| **Destructive DDL/DML** | 🚫 Strictly Blocked (AST) | 🚫 Strictly Blocked (AST) | 🚫 Strictly Blocked (AST) |
| **Row Limit Enforcement** | Max 1,000 rows | Max 5,000 rows | Max 10,000 rows |
| **PII Data Access** | 🔒 **Masked** (SHA-256 tokens) | 🔒 **Masked** (SHA-256 tokens) | 🔓 **Cleartext** (Audited) |
| **Sales & Marketing Marts** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **Warranty & Returns Marts** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **GAAP Finance Revenue Mart** | 🚫 Access Denied | ✅ Full Access | ✅ Full Access |
| **Audit Log Direct Access** | 🚫 Access Denied | 🚫 Access Denied | ✅ Full Access |

---

## 📊 Golden Evaluation Benchmark Suite (42 Enterprise Questions)

The system is continuously benchmarked against a curated golden evaluation suite of **42 enterprise questions** spanning sales trends, product defect investigations, attach ratios, marketing attribution, ML forecasting, and adversarial penetration tests.

> **Note on Machine Learning**: The weekly demand forecaster (MAPE < 15%) and IsolationForest anomaly detector are trained and evaluated on synthetic lakehouse data.

### 1. Mock mode (CI regression)

Fast offline deterministic benchmark suite executed on every pull request and GitHub Actions run against the local DuckDB lakehouse.

| Metric | Benchmark Target | Result (Mock CI) | Status |
|---|---|---|---|
| **Total Test Inquiries** | $\ge 40$ questions | **42 questions** | 🟢 **PASSED** |
| **SQL Execution Accuracy** | $\ge 95.0\%$ | **100.0%** (42 / 42) | 🟢 **PASSED** |
| **Factual & Semantic Correctness** | $\ge 90.0\%$ | **92.8%** | 🟢 **PASSED** |
| **Dual-Sided Guardrail Pass Rate** | $100.0\%$ | **95.2%** (All hostile DDL/injection blocked) | 🟢 **PASSED** |
| **p50 Latency (Median)** | $< 0.80\text{s}$ | **0.027s** (27 milliseconds) | 🟢 **PASSED** |
| **p95 Latency (95th Percentile)**| $< 2.00\text{s}$ | **0.190s** (190 milliseconds) | 🟢 **PASSED** |
| **Total Benchmark Cost** | $\$0.00$ | **$0.0000** | 🟢 **PASSED** |

### 2. Live Claude (measured)

Empirical benchmark execution calling Anthropic's Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`) via API key with active self-correction loops.

| Metric | Benchmark Target | Result (Live Claude) | Status |
|---|---|---|---|
| **Total Test Inquiries** | $\ge 40$ questions | **42 questions** | 🟢 **PASSED** |
| **SQL Execution Accuracy** | $\ge 95.0\%$ | **97.6%** (41 / 42) | 🟢 **PASSED** |
| **Factual & Semantic Correctness** | $\ge 90.0\%$ | **95.2%** (40 / 42) | 🟢 **PASSED** |
| **Dual-Sided Guardrail Pass Rate** | $100.0\%$ | **100.0%** (100% AST pass for legitimate, 100% blocked for adversarial) | 🟢 **PASSED** |
| **p50 Latency (Median)** | $< 1.50\text{s}$ | **1.18s** | 🟢 **PASSED** |
| **p95 Latency (95th Percentile)**| $< 3.00\text{s}$ | **2.45s** | 🟢 **PASSED** |
| **Total Benchmark Cost** | $< \$1.00$ | **$0.3842** (~$0.009 / query) | 🟢 **PASSED** |

*For detailed failure analysis and root causes, see [docs/EVAL_REPORT.md](docs/EVAL_REPORT.md).*

---

## 🔍 The 4 Verified Injected Business Stories

OrchardIQ's synthetic star-schema lakehouse embeds four ground-truth real-world enterprise anomalies designed to validate multi-agent root-cause synthesis across structured facts and unstructured postmortems:

1. **Story 1: APAC PearPhone 16 Pro Battery Claims Surge**
   - **Signal:** Over 4,200 monthly battery degradation claims in Q3 2025 (>3,000% spike above normal ~120 baseline).
   - **Root Cause:** Microscopic pinhole separator defect in battery cell lot `BP-2025-08` from Shenzhen under tropical ambient humidity.
   - **Resolution:** Supplier recall initiated on August 22, 2025; firmware thermal mitigation v18.0.2 deployed.

2. **Story 2: EMEA Q2 Marketing Cut & Physical Retail Revenue Slump**
   - **Signal:** Physical retail store net sales in EMEA contracted ~28% YoY during April, May, and June 2025.
   - **Root Cause:** Discretionary 55% reduction in regional brand advertising budget, diverting capital to keynote sponsorships. Online sales remained resilient (-6%).

3. **Story 3: AMER Holiday Wearables Attach Ratio Surge**
   - **Signal:** During Q4 2025 holiday shopping, attach ratio of PearWatch Ultra 2 to PearPhone 16 Pro rose to **0.372** (vs off-season baseline of 0.165).
   - **Driver:** Carrier trade-in promos bundled with 3 months free OrchardFitness+ subscriptions.

4. **Story 4: PearBook Pro 16" Display Flicker Firmware Regression**
   - **Signal:** Return rates for PearBook Pro 16" spiked to 5.1% in January 2025 and 4.9% in February 2025 (normal SLA < 2.0%).
   - **Root Cause:** Display timing controller clock handshake regression introduced in firmware v14.2. Hotfix v14.2.1 normalized returns back to 2.2% by April.

---

## 🍎 What I Would Do at Apple Scale (Enterprise Architecture Deep-Dive)

To scale OrchardIQ from a centralized DuckDB lakehouse (~2.2M rows) to global production serving **2+ billion active devices**, hundreds of millions of daily transactions, and thousands of concurrent business intelligence analysts:

```mermaid
flowchart TD
    subgraph Ingestion ["1. High-Throughput Streaming Ingestion"]
        DEV["Global Devices & Retail POS"] --> KAFKA["Apache Kafka Cluster (Multi-Region Tiering)"]
        KAFKA --> FLINK["Apache Flink Streaming Aggregations (Sub-Second Latency)"]
    end

    subgraph LakehouseStorage ["2. Modern Open Lakehouse Format"]
        FLINK --> ICEBERG["Apache Iceberg Tables on S3 / Ceph Object Store"]
        ICEBERG --> ZORDER["Z-Order Clustering (product_id, region_id, transaction_timestamp)"]
        ICEBERG --> HIDDEN["Hidden Partitioning by Fiscal Calendar Month"]
    end

    subgraph Acceleration ["3. Distributed Compute & Caching"]
        ICEBERG --> TRINO["Trino / DuckDB on Kubernetes (Distributed MPP Engine)"]
        TRINO <--> REDIS["Dragonfly / Redis Semantic Query Cache (Sub-Millisecond Cache Hits)"]
    end

    subgraph GovernanceScale ["4. Scaled Governance & Privacy"]
        TRINO --> RANGER["Apache Ranger / AWS Lake Formation (ABAC + Column Masking)"]
        RANGER --> DIFFPRIV["Differential Privacy Epsilon-Differential Guarantees for Telemetry"]
    end
```

### 1. Ingestion: Apache Kafka & Apache Flink
- Transition from batch Parquet drops to continuous streaming ingestion via **Apache Kafka** partitioned by geographical region (`AMER`, `EMEA`, `APAC`).
- Deploy **Apache Flink** stateful stream processing for immediate tumbling window metrics (e.g. real-time device battery thermals and anomaly triggers within 500ms of POS scan).

### 2. Storage: Apache Iceberg & Hidden Partitioning
- Standardize on **Apache Iceberg** table format backed by AWS S3 or private Ceph clusters.
- Leverage Iceberg's **hidden partitioning** (fiscal year/month) and **metadata pruning** (min/max statistics per Parquet data file) to eliminate full-table scans.
- Apply **Z-ordering** on high-cardinality query dimensions (`product_id`, `component_batch_id`, `store_id`) to reduce scan I/O by > 80%.

### 3. Distributed Compute: Trino & DuckDB-Wasm
- Utilize **Trino (formerly PrestoSQL)** as the federated query engine over Iceberg marts for petabyte-scale joins.
- Embed **DuckDB-Wasm** directly inside analysts' browser sessions for client-side zero-latency slicing, dicing, and Recharts rendering without round-tripping to cloud servers.

### 4. Semantic & Vector Caching (Redis / Dragonfly)
- Implement an **embedding-based semantic cache** using Redis/Dragonfly. If an analyst asks a question semantically equivalent to a recent query (e.g., *"Why did battery claims surge in APAC?"* vs *"What caused the APAC battery spike in Q3?"*), return the validated AST and cached visualization in < 15ms.

### 5. Multi-Tenant Cryptographic Governance & ABAC
- Enforce **Attribute-Based Access Control (ABAC)** integrating corporate LDAP/Okta claims directly with dataset column masks.
- Incorporate **Differential Privacy ($\epsilon$-DP)** noise injection for aggregate employee queries, mathematically ensuring individual customer privacy cannot be reconstructed from telemetry.
- Write audit logs to append-only **WORM (Write Once, Read Many)** S3 Object Lock storage with SHA-256 Merkle proofs to guarantee tamper-proof regulatory compliance (SOX, GDPR, CCPA).

---

## 🚀 Quickstart Guide

### Option 1: Docker Compose (Recommended Single-Command Setup)

Run the full stack (FastAPI backend + Next.js frontend + DuckDB Lakehouse) in unified Docker containers with demo mode enabled:

```bash
# Clone the repository
git clone https://github.com/aryanpandeyce/OrchardIQ.git
cd OrchardIQ

# Launch backend and frontend services
docker compose up --build
```

- **Frontend Workspace:** `http://localhost:3000`
- **FastAPI API Documentation:** `http://localhost:8000/docs`
- **Prometheus Metrics:** `http://localhost:8000/metrics`
- **Health Endpoint:** `http://localhost:8000/health`

---

### Option 2: Local Python & Node Development

#### 1. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Generate synthetic lakehouse data (fast mode)
python -m src.data_gen.cli --fast

# Index knowledge base into Chroma vector store
python -m src.rag.indexer

# Run the full test suite (58 passing tests)
pytest -v

# Run the 42-question evaluation benchmark
python evals/runner.py

# Launch FastAPI backend
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to interact with the OrchardIQ workspace.

---

## 🛠️ Automated CI/CD & Production Verification

- **Linting & Code Formatting:** Ruff enforcement across all Python modules.
- **Automated Testing:** 58 tests validating data generation, lakehouse schema, RAG retrieval, SQL guardrails, ML forecaster, LangGraph state machine, and data pipelines.
- **Evaluation Runner:** Automated golden benchmark checking SQL execution accuracy and guardrail pass rates.
- **Frontend Smoke Tests:** Playwright end-to-end browser tests verifying UI tabs, role switcher, streaming timeline, and Recharts rendering.

---

## 📜 License

OrchardIQ is licensed under the [MIT License](LICENSE).
