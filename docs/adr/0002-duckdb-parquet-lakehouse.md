# ADR 0002: DuckDB Over Partitioned Parquet Lakehouse Architecture

## Status
Accepted

## Date
2026-10-28

## Context
OrchardIQ requires an analytical data engine to power multi-agent natural language data exploration, SQL generation, statistical period-over-period computations, and anomaly checks across ~2,000,000 fact rows and multiple dimensions.
The solution must:
1. Deliver sub-second query latency for interactive conversational agent flows.
2. Support standard ANSI SQL with rich window functions, CTEs, and date arithmetic.
3. Run fully locally for deterministic development, testing, and offline demos without requiring external database servers or Docker overhead.
4. Scale seamlessly to cloud deployments (AWS S3 lakehouse or AWS ECS) with zero schema migration.

## Alternatives Considered
1. **PostgreSQL / SQLite**:
   - *Pros*: Mature, pervasive, simple local setup.
   - *Cons*: Row-oriented storage exhibits poor scan performance on aggregations over millions of rows. Lacks native partitioned Parquet pushdown. SQLite lacks analytical window functions and decimal precision.
2. **Snowflake / AWS Redshift / Databricks**:
   - *Pros*: Enterprise standard for cloud OLAP.
   - *Cons*: Expensive running costs, network latency, credential dependency for portfolio review, impossible to run deterministic tests in offline/CI environments without expensive mocks.
3. **DuckDB over Hive-Partitioned Parquet Files**:
   - *Pros*: In-process vectorized columnar query execution engine; native direct querying of Parquet files via `read_parquet()`; automatic partition pruning via directory paths (`year=YYYY/month=MM`); zero-copy Apache Arrow interoperability for ML models; native S3 support via `httpfs` extension; sub-50ms execution times on millions of rows; zero running infrastructure cost.
   - *Cons*: Single-writer concurrency model for raw file modifications (mitigated because the analytical warehouse layer in OrchardIQ is read-only for analytical agents).

## Decision
We choose **DuckDB querying Hive-partitioned Parquet datasets** (`marts/`) as the core lakehouse storage and query execution layer.

- Parquet files are stored locally in `data/warehouse/marts/` partitioned by `year=YYYY/month=MM` for transactional facts (`fact_sales`, `fact_returns`, `fact_support_claims`, `fact_marketing_spend`).
- DuckDB views are registered over the Parquet datasets using `read_parquet(..., hive_partitioning=true)`.
- For production AWS deployment, the `S3_ENDPOINT` and `S3_BUCKET` configuration parameters redirect views to S3 paths (`s3://orchardiq-lakehouse-prod/marts/...`) using DuckDB's `httpfs` extension.

## Consequences & Trade-offs
### Positive
- **Blazing Performance**: Aggregations across 2M rows complete in 15–40 milliseconds.
- **Portability**: Developers and hiring managers can clone the repository, run `orchardiq-generate`, and execute queries immediately without spinning up database containers.
- **Standard SQL**: Full ANSI SQL compatibility parsed and validated cleanly with `sqlglot`.
- **Zero-Copy ML Transfer**: DuckDB results export directly to PyArrow and PyTorch tensors without serialization overhead.

### Negative / Mitigations
- In-process writes: Handled by generating read-optimized Parquet datasets in batch ETL rather than executing concurrent transactional INSERTs.
