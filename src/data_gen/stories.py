"""Injected stories and ground-truth business anomalies for OrchardIQ."""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass(frozen=True)
class InjectedStory:
    story_id: str
    title: str
    quarter: str
    target_period: str
    affected_entity: str
    region_id: str
    root_cause: str
    component_batch_id: str
    verification_query: str
    expected_finding: str


INJECTED_STORIES: List[InjectedStory] = [
    InjectedStory(
        story_id="STORY-01-APAC-CLAIMS",
        title="APAC Q3 2025 Battery Degradation Claims Spike",
        quarter="2025-Q3",
        target_period="2025-07-01 to 2025-09-30",
        affected_entity="PRD-PHN-16P (PearPhone 16 Pro)",
        region_id="APAC",
        root_cause="Cathode contamination in supplier battery lot BP-2025-08 caused elevated thermal resistance and premature battery swelling under fast charging.",
        component_batch_id="BP-2025-08",
        verification_query="""
            SELECT 
                COUNT(*) as total_claims,
                COUNT(CASE WHEN claim_type = 'Battery Degradation/Thermal' THEN 1 END) as battery_claims,
                COUNT(CASE WHEN component_batch_id = 'BP-2025-08' THEN 1 END) as defective_lot_claims,
                ROUND(COUNT(CASE WHEN claim_type = 'Battery Degradation/Thermal' THEN 1 END) * 100.0 / COUNT(*), 2) as battery_pct
            FROM fact_support_claims
            WHERE region_id = 'APAC' 
              AND product_id = 'PRD-PHN-16P'
              AND year = 2025 AND month IN (7, 8, 9)
        """,
        expected_finding="Battery claims represent > 50% of all claims for PearPhone 16 Pro in APAC in Q3 2025, heavily concentrated in lot BP-2025-08."
    ),
    InjectedStory(
        story_id="STORY-02-EMEA-MARKETING-DIP",
        title="EMEA Q2 2025 Marketing Spend Slump Causing Retail Sales Contraction",
        quarter="2025-Q2",
        target_period="2025-04-01 to 2025-06-30",
        affected_entity="Retail Channel Sales in EMEA",
        region_id="EMEA",
        root_cause="Marketing budget was reallocated to North American WWPC keynote sponsorships, cutting EMEA digital search and social spend by 65%. Retail foot traffic and sales contracted by ~25%.",
        component_batch_id="N/A",
        verification_query="""
            WITH mkt AS (
                SELECT 
                    year, 
                    CASE WHEN month IN (4,5,6) THEN 'Q2' ELSE 'Other' END as quarter_bucket,
                    SUM(spend_usd) as total_spend
                FROM fact_marketing_spend
                WHERE region_id = 'EMEA' AND year = 2025
                GROUP BY 1, 2
            ),
            sales AS (
                SELECT 
                    year,
                    CASE WHEN month IN (4,5,6) THEN 'Q2' ELSE 'Other' END as quarter_bucket,
                    SUM(net_revenue) as retail_net_rev
                FROM fact_sales
                WHERE region_id = 'EMEA' AND channel = 'Retail' AND year = 2025
                GROUP BY 1, 2
            )
            SELECT 
                mkt.quarter_bucket,
                mkt.total_spend,
                sales.retail_net_rev
            FROM mkt
            JOIN sales ON mkt.quarter_bucket = sales.quarter_bucket
        """,
        expected_finding="EMEA Q2 2025 marketing spend drops below $800k (vs ~$2.5M in other quarters), driving a retail revenue contraction of ~25%."
    ),
    InjectedStory(
        story_id="STORY-03-AMER-ATTACH-SURGE",
        title="AMER Q4 2025 PearWatch Ultra 2 Holiday Attach-Rate Surge",
        quarter="2025-Q4",
        target_period="2025-10-01 to 2025-12-31",
        affected_entity="PRD-WCH-ULT2 paired with PRD-PHN-16P",
        region_id="AMER",
        root_cause="The 'Orchard Adventure Pro' holiday promotional bundle offered a $150 credit towards PearWatch Ultra 2 with any PearPhone 16 Pro activation.",
        component_batch_id="N/A",
        verification_query="""
            SELECT 
                year,
                CASE WHEN month IN (10, 11, 12) THEN 'Q4' ELSE 'Non-Q4' END as period,
                SUM(CASE WHEN product_id = 'PRD-PHN-16P' THEN units ELSE 0 END) as phone_units,
                SUM(CASE WHEN product_id = 'PRD-WCH-ULT2' THEN units ELSE 0 END) as watch_units,
                ROUND(SUM(CASE WHEN product_id = 'PRD-WCH-ULT2' THEN units ELSE 0 END) * 1.0 / 
                      NULLIF(SUM(CASE WHEN product_id = 'PRD-PHN-16P' THEN units ELSE 0 END), 0), 3) as attach_ratio
            FROM fact_sales
            WHERE region_id = 'AMER' AND year = 2025
            GROUP BY 1, 2
        """,
        expected_finding="Attach ratio of PearWatch Ultra 2 to PearPhone 16 Pro in AMER Q4 exceeds 0.35 (vs baseline ~0.12 in other quarters)."
    ),
    InjectedStory(
        story_id="STORY-04-PEARBOOK-FLICKER",
        title="PearBook Pro 16\" Q1 2025 Display Flicker Return Surge",
        quarter="2025-Q1",
        target_period="2025-01-15 to 2025-02-28",
        affected_entity="PRD-NBK-16P (PearBook Pro 16\")",
        region_id="GLOBAL",
        root_cause="Firmware patch v14.2 introduced a DisplayPort 2.1 handshake timing bug that caused screen flicker on external 6K monitors.",
        component_batch_id="N/A",
        verification_query="""
            SELECT 
                s.year,
                s.month,
                COUNT(DISTINCT s.sale_id) as sales_count,
                COUNT(DISTINCT r.return_id) as returns_count,
                ROUND(COUNT(DISTINCT r.return_id) * 100.0 / NULLIF(COUNT(DISTINCT s.sale_id), 0), 2) as return_rate_pct
            FROM fact_sales s
            LEFT JOIN fact_returns r 
              ON s.sale_id = r.sale_id 
             AND r.return_reason = 'Defective / Hardware Issue'
            WHERE s.product_id = 'PRD-NBK-16P' AND s.year = 2025
            GROUP BY s.year, s.month
            ORDER BY s.month
        """,
        expected_finding="Return rate for PearBook Pro 16\" spikes to > 7% in Jan/Feb 2025 before dropping back to baseline < 2.5% in March following firmware hotfix v14.2.1."
    ),
]
