"""LLM Provider abstraction supporting Anthropic Claude and deterministic MockLLM."""

import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import httpx

from src.config import Settings, settings


@dataclass
class LLMResponse:
    """Encapsulates model generation content, token usage, latency, and cost."""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_estimate_usd: float


class LLMProvider(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Generate response text from prompt."""
        pass


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider using HTTPX."""

    API_URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for ClaudeProvider.")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        t0 = time.perf_counter()
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(self.API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        content_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content_text += block.get("text", "")

        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens

        # Pricing estimate ($3/M input, $15/M output for Sonnet)
        cost = (prompt_tokens * 3.0 / 1e6) + (completion_tokens * 15.0 / 1e6)

        return LLMResponse(
            content=content_text,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_estimate_usd=round(cost, 6),
        )


class MockLLMProvider(LLMProvider):
    """
    Deterministic Mock LLM for offline demonstration, unit testing, and eval harness.
    Synthesizes valid DuckDB SQL, self-corrections, and executive narratives without external API calls.
    """

    def __init__(self, model_name: str = "orchard-mock-llm-v1"):
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResponse:
        t0 = time.perf_counter()
        p_lower = prompt.lower()
        content = ""

        # 1. Self-Correction Detection
        if "error:" in p_lower or "failed:" in p_lower:
            if "prd-phn-16p" in p_lower or "apac" in p_lower or "battery" in p_lower:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    claim_type, \n"
                    "    component_batch_id, \n"
                    "    COUNT(*) as claim_count, \n"
                    "    ROUND(AVG(repair_cost), 2) as avg_cost \n"
                    "FROM fact_support_claims \n"
                    "WHERE region_id = 'APAC' AND product_id = 'PRD-PHN-16P' AND year = 2025 AND month IN (7, 8, 9) \n"
                    "GROUP BY 1, 2 \n"
                    "ORDER BY claim_count DESC;\n"
                    "```"
                )
            else:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    p.category, \n"
                    "    COUNT(*) as total_sales, \n"
                    "    ROUND(SUM(s.net_revenue), 2) as total_net_revenue \n"
                    "FROM fact_sales s \n"
                    "JOIN dim_product p ON s.product_id = p.product_id \n"
                    "GROUP BY 1 \n"
                    "ORDER BY total_net_revenue DESC;\n"
                    "```"
                )

        # 2. Injected Story 1: APAC Q3 2025 Battery Degradation
        elif "apac" in p_lower and ("battery" in p_lower or "claim" in p_lower or "bp-2025-08" in p_lower or "spike" in p_lower):
            if "narrator" in (system_prompt or "").lower() or "synthesize" in p_lower:
                content = (
                    "### Executive Summary\n"
                    "During Q3 2025, Orchard Support Operations detected an acute 4.5x surge in warranty claims for PearPhone 16 Pro in the APAC region. "
                    "Over 52% of all device claims in APAC were categorized under **Battery Degradation/Thermal**, heavily concentrated in supplier lot **BP-2025-08** from Shenzhen.\n\n"
                    "### Key Findings\n"
                    "- **Defective Lot**: Lot BP-2025-08 accounted for the vast majority of battery claims due to cathode electrolyte contamination.\n"
                    "- **Total Service Cost**: Internal repair expenditures in APAC reached over $1.2M before inventory isolation on August 22.\n"
                    "- **Remediation**: Genius Bar authorized free battery module replacements, normalizing claim volumes by early Q4."
                )
            else:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    claim_type, \n"
                    "    component_batch_id, \n"
                    "    COUNT(*) as total_claims, \n"
                    "    ROUND(AVG(repair_cost), 2) as avg_repair_cost \n"
                    "FROM fact_support_claims \n"
                    "WHERE region_id = 'APAC' AND product_id = 'PRD-PHN-16P' AND year = 2025 AND month IN (7, 8, 9) \n"
                    "GROUP BY 1, 2 \n"
                    "ORDER BY total_claims DESC;\n"
                    "```"
                )

        # 3. Injected Story 2: EMEA Q2 2025 Marketing Spend Slump
        elif "emea" in p_lower and ("marketing" in p_lower or "slump" in p_lower or "retail" in p_lower or "q2" in p_lower):
            if "narrator" in (system_prompt or "").lower() or "synthesize" in p_lower:
                content = (
                    "### Executive Summary\n"
                    "In Q2 2025, EMEA retail store net revenue contracted by approximately 24% compared to previous quarters. "
                    "Data analysis demonstrates this was directly driven by a 65% reduction in regional marketing expenditure as funds were diverted to North American developer conference sponsorships.\n\n"
                    "### Key Findings\n"
                    "- **Marketing Cut**: EMEA monthly spend dropped from ~$2.4M to ~$750K in April–June 2025.\n"
                    "- **Retail Foot Traffic**: Foot traffic and physical retail sales fell sharply, whereas online store sales experienced less disruption.\n"
                    "- **Rebound**: Normalizing marketing allocations in Q3 restored retail revenue trajectory."
                )
            else:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    month, \n"
                    "    ROUND(SUM(spend_usd), 2) as monthly_marketing_spend \n"
                    "FROM fact_marketing_spend \n"
                    "WHERE region_id = 'EMEA' AND year = 2025 \n"
                    "GROUP BY 1 \n"
                    "ORDER BY 1;\n"
                    "```"
                )

        # 4. Injected Story 3: AMER Q4 2025 PearWatch Ultra Holiday Attach Surge
        elif "attach" in p_lower or ("pearwatch" in p_lower and "ultra" in p_lower and "q4" in p_lower):
            if "narrator" in (system_prompt or "").lower() or "synthesize" in p_lower:
                content = (
                    "### Executive Summary\n"
                    "During the Q4 2025 holiday shopping quarter, PearWatch Ultra 2 attach rates to PearPhone 16 Pro activations in AMER surged to **41.2%**, "
                    "nearly tripling the baseline rate of 13.8%.\n\n"
                    "### Key Findings\n"
                    "- **Promotional Driver**: The 'Orchard Adventure Pro' $150 bundle credit drove substantial cross-device adoption.\n"
                    "- **Margin Contribution**: High margin on flagship phones offset the bundle credit, yielding a net 14% lift in overall transaction profit."
                )
            else:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    CASE WHEN month IN (10, 11, 12) THEN 'Q4 Holiday' ELSE 'Non-Q4' END as period, \n"
                    "    SUM(CASE WHEN product_id = 'PRD-PHN-16P' THEN units ELSE 0 END) as phone_units, \n"
                    "    SUM(CASE WHEN product_id = 'PRD-WCH-ULT2' THEN units ELSE 0 END) as watch_units, \n"
                    "    ROUND(SUM(CASE WHEN product_id = 'PRD-WCH-ULT2' THEN units ELSE 0 END) * 1.0 / NULLIF(SUM(CASE WHEN product_id = 'PRD-PHN-16P' THEN units ELSE 0 END), 0), 3) as attach_rate \n"
                    "FROM fact_sales \n"
                    "WHERE region_id = 'AMER' AND year = 2025 \n"
                    "GROUP BY 1;\n"
                    "```"
                )

        # 5. Injected Story 4: PearBook Pro 16" Q1 2025 Display Flicker Returns
        elif "pearbook" in p_lower and ("flicker" in p_lower or "return" in p_lower or "v14.2" in p_lower or "defect" in p_lower):
            if "narrator" in (system_prompt or "").lower() or "synthesize" in p_lower:
                content = (
                    "### Executive Summary\n"
                    "Return rates for PearBook Pro 16\" spiked to over 7% in January and February 2025, driven by customer complaints of screen flickering on external displays. "
                    "The issue was traced to DisplayPort clock synchronization timing introduced in PearOS firmware patch v14.2.\n\n"
                    "### Key Findings\n"
                    "- **Hardware Diagnosis**: Customers initially suspected discrete GPU defects, increasing return requests.\n"
                    "- **Software Resolution**: Firmware hotfix v14.2.1 released on Feb 24 permanently corrected the timing handshake, returning return rates to < 2.5%."
                )
            else:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    CAST(s.month AS INTEGER) as month, \n"
                    "    COUNT(DISTINCT s.sale_id) as sales_count, \n"
                    "    COUNT(DISTINCT r.return_id) as defective_returns, \n"
                    "    ROUND(COUNT(DISTINCT r.return_id) * 100.0 / NULLIF(COUNT(DISTINCT s.sale_id), 0), 2) as defect_return_rate \n"
                    "FROM fact_sales s \n"
                    "LEFT JOIN fact_returns r ON s.sale_id = r.sale_id AND r.return_reason = 'Defective / Hardware Issue' \n"
                    "WHERE s.product_id = 'PRD-NBK-16P' AND s.year = 2025 \n"
                    "GROUP BY 1 \n"
                    "ORDER BY 1;\n"
                    "```"
                )

        # 6. Customer PII Query
        elif "customer" in p_lower or "pii" in p_lower or "membership" in p_lower:
            content = (
                "```sql\n"
                "SELECT \n"
                "    customer_id, \n"
                "    first_name, \n"
                "    last_name, \n"
                "    email, \n"
                "    phone, \n"
                "    city, \n"
                "    customer_segment \n"
                "FROM dim_customer \n"
                "LIMIT 10;\n"
                "```"
            )

        # Unauthorized Table Check
        elif "unauthorized_table" in p_lower:
            content = "```sql\nSELECT customer_id, ssn, credit_card_num FROM unauthorized_table;\n```"

        # Analyst Access to Finance Ledger Check
        elif "can an analyst access" in p_lower and "fact_finance_revenue" in p_lower:
            content = "```sql\nSELECT * FROM fact_finance_revenue LIMIT 5;\n```"

        # 7. Warranty & Support Claims
        elif "claim" in p_lower or "warranty" in p_lower or "repair" in p_lower:
            if "cost" in p_lower:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    product_id, \n"
                    "    COUNT(*) as total_claims, \n"
                    "    ROUND(SUM(repair_cost), 2) as total_claim_cost \n"
                    "FROM fact_support_claims \n"
                    "WHERE year = 2025 \n"
                    "GROUP BY 1 \n"
                    "ORDER BY total_claim_cost DESC \n"
                    "LIMIT 5;\n"
                    "```"
                )
            elif "type" in p_lower:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    claim_type, \n"
                    "    COUNT(*) as count \n"
                    "FROM fact_support_claims \n"
                    "WHERE year = 2025 \n"
                    "GROUP BY 1 \n"
                    "ORDER BY count DESC;\n"
                    "```"
                )
            else:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    COUNT(*) as total_claims, \n"
                    "    ROUND(SUM(repair_cost), 2) as total_cost \n"
                    "FROM fact_support_claims \n"
                    "WHERE year = 2025;\n"
                    "```"
                )

        # 8. Returns & Quality
        elif "return" in p_lower or "refund" in p_lower:
            if "reason" in p_lower:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    return_reason, \n"
                    "    COUNT(*) as count \n"
                    "FROM fact_returns \n"
                    "WHERE year = 2025 \n"
                    "GROUP BY 1 \n"
                    "ORDER BY count DESC;\n"
                    "```"
                )
            elif "refund" in p_lower:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    ROUND(SUM(refund_amount), 2) as total_refunds \n"
                    "FROM fact_returns \n"
                    "WHERE year = 2025;\n"
                    "```"
                )
            else:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_sales WHERE year = 2025), 2) as return_rate \n"
                    "FROM fact_returns \n"
                    "WHERE year = 2025;\n"
                    "```"
                )

        # 9. Marketing Spend
        elif "marketing" in p_lower or "campaign" in p_lower or "spend" in p_lower or "ad" in p_lower:
            content = (
                "```sql\n"
                "SELECT \n"
                "    channel, \n"
                "    ROUND(SUM(spend_usd), 2) as total_spend \n"
                "FROM fact_marketing_spend \n"
                "WHERE year = 2025 \n"
                "GROUP BY 1 \n"
                "ORDER BY total_spend DESC;\n"
                "```"
            )

        # 10. Finance / GAAP Ledger
        elif "gaap" in p_lower or "finance" in p_lower or "recognized" in p_lower or "deferred" in p_lower:
            content = (
                "```sql\n"
                "SELECT \n"
                "    fiscal_quarter, \n"
                "    ROUND(SUM(recognized_net_revenue), 2) as recognized_net_revenue, \n"
                "    ROUND(SUM(deferred_services_revenue), 2) as deferred_services_revenue \n"
                "FROM fact_finance_revenue \n"
                "WHERE fiscal_year = 2025 \n"
                "GROUP BY 1 \n"
                "ORDER BY 1;\n"
                "```"
            )

        # 11. Discounts & Channels
        elif "discount" in p_lower:
            content = (
                "```sql\n"
                "SELECT \n"
                "    ROUND(SUM(discount_amount), 2) as total_discount \n"
                "FROM fact_sales \n"
                "WHERE year = 2025;\n"
                "```"
            )
        elif "channel" in p_lower or "online" in p_lower or "retail store" in p_lower:
            content = (
                "```sql\n"
                "SELECT \n"
                "    channel, \n"
                "    ROUND(SUM(net_revenue), 2) as channel_revenue \n"
                "FROM fact_sales \n"
                "WHERE year = 2025 \n"
                "GROUP BY 1 \n"
                "ORDER BY channel_revenue DESC;\n"
                "```"
            )
        elif "total net revenue" in p_lower or "fy 2025 across all" in p_lower:
            content = (
                "```sql\n"
                "SELECT \n"
                "    ROUND(SUM(net_revenue), 2) as total_net_revenue \n"
                "FROM fact_sales \n"
                "WHERE year = 2025;\n"
                "```"
            )

        # 12. General Revenue / Top Products Query
        else:
            if "narrator" in (system_prompt or "").lower() or "synthesize" in p_lower:
                content = (
                    "### Executive Summary\n"
                    "Across the product line, PearPhone 16 Pro Max and PearPhone 16 Pro represent the primary revenue drivers, generating over 55% of total gross proceeds. "
                    "Hardware gross margins remain robust at 42.5%.\n\n"
                    "### Recommended Follow-Ups\n"
                    "1. Would you like a regional breakdown between AMER, EMEA, and APAC?\n"
                    "2. Should we generate a 6-week demand forecast for PearPhone 16 Pro?"
                )
            else:
                content = (
                    "```sql\n"
                    "SELECT \n"
                    "    p.product_name, \n"
                    "    p.category, \n"
                    "    SUM(s.units) as units_sold, \n"
                    "    ROUND(SUM(s.net_revenue), 2) as net_revenue_usd \n"
                    "FROM fact_sales s \n"
                    "JOIN dim_product p ON s.product_id = p.product_id \n"
                    "GROUP BY 1, 2 \n"
                    "ORDER BY net_revenue_usd DESC \n"
                    "LIMIT 10;\n"
                    "```"
                )

        latency_ms = round((time.perf_counter() - t0) * 1000 + 12.0, 2)
        words = content.split()
        tokens = len(words) * 2

        return LLMResponse(
            content=content,
            model=self.model_name,
            prompt_tokens=len(prompt.split()) * 2,
            completion_tokens=tokens,
            total_tokens=tokens + len(prompt.split()) * 2,
            latency_ms=latency_ms,
            cost_estimate_usd=0.0,
        )


def get_llm_provider(config: Optional[Settings] = None) -> LLMProvider:
    """Return configured LLM provider: Claude if key available and mock disabled, else MockLLM."""
    cfg = config or settings
    api_key = cfg.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
    if api_key and not cfg.MOCK_LLM_MODE:
        try:
            return ClaudeProvider(api_key=api_key)
        except Exception:
            return MockLLMProvider()
    return MockLLMProvider()
