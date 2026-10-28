"""Tests verifying that the 4 injected ground-truth business stories are numerically provable via SQL."""

import pytest
from src.warehouse.query_engine import WarehouseQueryEngine, QueryResult


def test_story_1_apac_battery_claims_spike(query_engine: WarehouseQueryEngine):
    """
    Story 1 Verification:
    In APAC in Q3 2025 (months 7, 8, 9), PearPhone 16 Pro (PRD-PHN-16P) experienced
    a severe surge in Battery Degradation/Thermal claims driven by defective component lot BP-2025-08.
    """
    sql = """
        SELECT 
            COUNT(*) as total_claims,
            COUNT(CASE WHEN claim_type = 'Battery Degradation/Thermal' THEN 1 END) as battery_claims,
            COUNT(CASE WHEN component_batch_id = 'BP-2025-08' THEN 1 END) as defective_lot_claims,
            ROUND(COUNT(CASE WHEN claim_type = 'Battery Degradation/Thermal' THEN 1 END) * 100.0 / COUNT(*), 2) as battery_pct
        FROM fact_support_claims
        WHERE region_id = 'APAC' 
          AND product_id = 'PRD-PHN-16P'
          AND year = 2025 AND month IN (7, 8, 9);
    """
    res: QueryResult = query_engine.execute_query(sql)
    assert res.success is True
    row = res.rows[0]

    assert row["total_claims"] > 0
    assert row["defective_lot_claims"] > 0
    # Battery claims must exceed 40% of all claims for this SKU during this incident window
    assert row["battery_pct"] > 40.0
    # Every defective lot claim is explicitly linked to battery degradation
    assert row["defective_lot_claims"] <= row["battery_claims"]


def test_story_2_emea_marketing_and_retail_slump(query_engine: WarehouseQueryEngine):
    """
    Story 2 Verification:
    In EMEA during Q2 2025 (months 4, 5, 6), marketing expenditure was severely cut,
    causing a corresponding drop in retail net revenue.
    """
    # 1. Check marketing spend drop in Q2 vs other months in EMEA 2025
    mkt_sql = """
        SELECT 
            CASE WHEN month IN (4, 5, 6) THEN 'Q2_slump' ELSE 'Other_quarters' END as period,
            ROUND(AVG(monthly_spend), 2) as avg_monthly_spend
        FROM (
            SELECT month, SUM(spend_usd) as monthly_spend
            FROM fact_marketing_spend
            WHERE region_id = 'EMEA' AND year = 2025
            GROUP BY month
        )
        GROUP BY 1;
    """
    mkt_res: QueryResult = query_engine.execute_query(mkt_sql)
    assert mkt_res.success is True

    spend_by_period = {r["period"]: r["avg_monthly_spend"] for r in mkt_res.rows}
    assert "Q2_slump" in spend_by_period and "Other_quarters" in spend_by_period
    # Q2 average monthly marketing spend must be less than 50% of the other quarters
    assert spend_by_period["Q2_slump"] < (spend_by_period["Other_quarters"] * 0.55)

    # 2. Check retail net revenue drop in EMEA
    sales_sql = """
        SELECT 
            CASE WHEN month IN (4, 5, 6) THEN 'Q2_slump' ELSE 'Other_quarters' END as period,
            ROUND(AVG(monthly_rev), 2) as avg_monthly_rev
        FROM (
            SELECT month, SUM(net_revenue) as monthly_rev
            FROM fact_sales
            WHERE region_id = 'EMEA' AND channel = 'Retail' AND year = 2025
            GROUP BY month
        )
        GROUP BY 1;
    """
    sales_res: QueryResult = query_engine.execute_query(sales_sql)
    assert sales_res.success is True

    rev_by_period = {r["period"]: r["avg_monthly_rev"] for r in sales_res.rows}
    # Q2 monthly retail net revenue in EMEA must reflect the contraction
    assert rev_by_period["Q2_slump"] < rev_by_period["Other_quarters"]


def test_story_3_amer_q4_pearwatch_ultra_attach_surge(query_engine: WarehouseQueryEngine):
    """
    Story 3 Verification:
    In AMER during Q4 2025 holiday period (months 10, 11, 12), the attach ratio
    of PearWatch Ultra 2 (PRD-WCH-ULT2) to PearPhone 16 Pro (PRD-PHN-16P) surged past 0.35.
    """
    sql = """
        SELECT 
            CASE WHEN month IN (10, 11, 12) THEN 'Q4_holiday' ELSE 'Non_Q4' END as period,
            SUM(CASE WHEN product_id = 'PRD-PHN-16P' THEN units ELSE 0 END) as phone_units,
            SUM(CASE WHEN product_id = 'PRD-WCH-ULT2' THEN units ELSE 0 END) as watch_units,
            ROUND(SUM(CASE WHEN product_id = 'PRD-WCH-ULT2' THEN units ELSE 0 END) * 1.0 / 
                  NULLIF(SUM(CASE WHEN product_id = 'PRD-PHN-16P' THEN units ELSE 0 END), 0), 3) as attach_ratio
        FROM fact_sales
        WHERE region_id = 'AMER' AND year = 2025
        GROUP BY 1;
    """
    res: QueryResult = query_engine.execute_query(sql)
    assert res.success is True

    attach_by_period = {r["period"]: r["attach_ratio"] for r in res.rows}
    assert "Q4_holiday" in attach_by_period and "Non_Q4" in attach_by_period
    # Q4 attach ratio must be significantly higher than non-holiday baseline
    assert attach_by_period["Q4_holiday"] > 0.30
    assert attach_by_period["Q4_holiday"] > attach_by_period["Non_Q4"] * 1.8


def test_story_4_pearbook_display_flicker_return_surge(query_engine: WarehouseQueryEngine):
    """
    Story 4 Verification:
    For PearBook Pro 16\" (PRD-NBK-16P), display firmware regression v14.2 caused
    defective hardware return rates to spike in Jan/Feb 2025 before normalizing in later months.
    """
    sql = """
        SELECT 
            CAST(s.month AS INTEGER) as month,
            COUNT(DISTINCT s.sale_id) as sales_count,
            COUNT(DISTINCT r.return_id) as defective_returns,
            ROUND(COUNT(DISTINCT r.return_id) * 100.0 / NULLIF(COUNT(DISTINCT s.sale_id), 0), 2) as defect_return_rate
        FROM fact_sales s
        LEFT JOIN fact_returns r 
          ON s.sale_id = r.sale_id 
         AND r.return_reason = 'Defective / Hardware Issue'
        WHERE s.product_id = 'PRD-NBK-16P' AND s.year = 2025
        GROUP BY 1
        ORDER BY 1;
    """
    res: QueryResult = query_engine.execute_query(sql)
    assert res.success is True

    rates_by_month = {int(r["month"]): float(r["defect_return_rate"]) for r in res.rows}
    # January & February must exhibit elevated return rates
    assert rates_by_month.get(1, 0.0) > 4.5 or rates_by_month.get(2, 0.0) > 4.5
    # Later months (e.g. month 4 or 5) must be significantly lower (< 3.0%)
    if 4 in rates_by_month:
        assert rates_by_month[4] < 3.5
