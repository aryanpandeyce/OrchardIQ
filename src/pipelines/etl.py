"""Batch ETL Orchestration Pipeline: raw -> staging -> marts with Data Quality Gates."""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.warehouse.query_engine import WarehouseQueryEngine
from src.pipelines.quality import DataQualityEngine


@dataclass
class ETLPipelineRunResult:
    """Output summary of an ETL batch run."""
    run_id: str
    status: str  # "SUCCESS", "FAILED_DQ_GATE", "ERROR"
    duration_ms: float
    raw_records_processed: int
    staging_records_cleansed: int
    marts_records_published: int
    dq_gate_status: str
    message: str


class BatchETLPipeline:
    """Orchestrates end-to-end lakehouse transformation raw -> staging -> marts with automated quality gates."""

    def __init__(
        self,
        query_engine: Optional[WarehouseQueryEngine] = None,
        dq_engine: Optional[DataQualityEngine] = None,
    ):
        self.query_engine = query_engine or WarehouseQueryEngine()
        self.dq_engine = dq_engine or DataQualityEngine(query_engine=self.query_engine)

    def execute_batch(self, batch_date: str = "2025-10-28") -> ETLPipelineRunResult:
        """Execute the multi-tier batch pipeline."""
        run_id = f"etl_{int(time.time())}"
        t0 = time.time()

        # Step 1: Raw Layer Ingestion / Validation
        raw_res = self.query_engine.execute_query("SELECT COUNT(*) as cnt FROM fact_sales WHERE year = 2025;")
        raw_count = int(raw_res.rows[0]["cnt"]) if raw_res.success and raw_res.rows else 0

        # Step 2: Staging Layer Cleansing & Deduplication
        # Simulates staging transformation view
        staging_sql = """
            SELECT 
                s.sale_id,
                s.date_id,
                s.customer_id,
                s.product_id,
                s.region_id,
                s.channel,
                s.units,
                s.gross_revenue,
                s.net_revenue,
                s.gross_margin,
                s.year,
                s.month
            FROM fact_sales s
            WHERE s.units > 0 AND s.net_revenue >= 0
            LIMIT 5000;
        """
        staging_res = self.query_engine.execute_query(staging_sql)
        staging_count = len(staging_res.rows) if staging_res.success else 0

        # Step 3: Automated Data Quality Gate
        dq_report = self.dq_engine.run_all_checks()
        dq_gate_passed = (dq_report["overall_status"] == "HEALTHY")

        if not dq_gate_passed:
            duration = round((time.time() - t0) * 1000, 2)
            return ETLPipelineRunResult(
                run_id=run_id,
                status="FAILED_DQ_GATE",
                duration_ms=duration,
                raw_records_processed=raw_count,
                staging_records_cleansed=staging_count,
                marts_records_published=0,
                dq_gate_status="FAILED",
                message="Pipeline aborted: Data Quality gate violations detected.",
            )

        # Step 4: Marts Layer Publishing
        # Materialize analytical mart summary: Monthly Sales & Margin by Region
        marts_sql = """
            SELECT 
                region_id,
                year,
                month,
                COUNT(sale_id) as total_transactions,
                SUM(units) as total_units,
                ROUND(SUM(net_revenue), 2) as net_revenue_usd,
                ROUND(SUM(gross_margin), 2) as gross_margin_usd
            FROM fact_sales
            WHERE year = 2025
            GROUP BY 1, 2, 3
            ORDER BY 1, 2, 3;
        """
        marts_res = self.query_engine.execute_query(marts_sql)
        marts_count = len(marts_res.rows) if marts_res.success else 0

        duration = round((time.time() - t0) * 1000, 2)
        return ETLPipelineRunResult(
            run_id=run_id,
            status="SUCCESS",
            duration_ms=duration,
            raw_records_processed=raw_count,
            staging_records_cleansed=staging_count,
            marts_records_published=marts_count,
            dq_gate_status="PASSED",
            message=f"Successfully processed {staging_count} records into marts ({marts_count} analytical aggregate partitions).",
        )
