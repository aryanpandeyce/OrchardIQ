/**
 * OrchardIQ Frontend API Client
 * Connects to FastAPI backend or provides deterministic demo-mode mock fallback.
 */

export interface StepLog {
  step_name: string;
  status: "RUNNING" | "COMPLETED" | "FAILED" | "SKIPPED";
  agent: string;
  message: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface AnswerPayload {
  session_id: string;
  run_id: string;
  narrative: string;
  visual_spec?: {
    chart_type: "bar" | "line" | "area";
    x_axis: string;
    series: string[];
    data: Record<string, unknown>[];
  } | null;
  sql_query?: string;
  data?: Record<string, unknown>[];
  citations?: {
    citation_id: string;
    title: string;
    doc_type: string;
    snippet: string;
    score: number;
  }[];
  governance: {
    status: string;
    role: string;
    audit_id: string;
    violations: string[];
  };
  steps: StepLog[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function askQuestionStream(
  query: string,
  role: string,
  onStep: (step: StepLog) => void,
  onAnswer: (answer: AnswerPayload) => void,
  onError?: (err: string) => void
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": `key-${role}`,
      },
      body: JSON.stringify({
        query,
        role,
        stream: true,
      }),
    });

    if (!res.ok) {
      throw new Error(`API returned ${res.status}: ${res.statusText}`);
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error("No readable stream");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const block of lines) {
        if (!block.trim()) continue;
        const eventMatch = block.match(/event:\s*(.+)/);
        const dataMatch = block.match(/data:\s*(.+)/);

        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1].trim();
          try {
            const data = JSON.parse(dataMatch[1].trim());
            if (eventType === "step") {
              onStep({
                step_name: data.agent || "Agent",
                agent: data.agent || "Agent",
                status: data.status || "COMPLETED",
                message: data.message || "",
                timestamp: Date.now() / 1000,
                metadata: data,
              });
            } else if (eventType === "answer") {
              onAnswer(data);
            }
          } catch {
            // Ignore parse errors on raw tokens
          }
        }
      }
    }
  } catch (err: unknown) {
    // If backend is not currently running or network error, provide instant demo mode fallback
    const errMsg = err instanceof Error ? err.message : String(err);
    console.warn("Backend offline or request failed, using instant demo mode fallback:", errMsg);
    onError?.(errMsg);
    await fallbackDemoExecution(query, role, onStep, onAnswer);
  }
}

async function fallbackDemoExecution(
  query: string,
  role: string,
  onStep: (step: StepLog) => void,
  onAnswer: (answer: AnswerPayload) => void
) {
  const steps: StepLog[] = [
    { step_name: "Planner", agent: "RouterPlanner", status: "COMPLETED", message: "Identified hybrid investigation intent. Formulated 5-step execution plan.", timestamp: Date.now() / 1000 },
    { step_name: "Catalog RAG", agent: "CatalogRAG", status: "COMPLETED", message: "Retrieved 4 relevant postmortems and component lot specs from knowledge base.", timestamp: Date.now() / 1000 },
    { step_name: "SQL Engine", agent: "SQLAgent", status: "COMPLETED", message: "Synthesized schema-grounded DuckDB SQL and executed against Lakehouse.", timestamp: Date.now() / 1000 },
    { step_name: "Governance Guardrails", agent: "GovernanceAgent", status: "COMPLETED", message: `AST validated (SELECT-only). Enforced RBAC column masking for role '${role}'.`, timestamp: Date.now() / 1000 },
    { step_name: "Narrator", agent: "NarratorAgent", status: "COMPLETED", message: "Executive narrative and interactive visual spec ready.", timestamp: Date.now() / 1000 },
  ];

  for (const s of steps) {
    onStep(s);
    await new Promise((r) => setTimeout(r, 120));
  }

  const qLower = query.toLowerCase();

  // Story 1
  if (qLower.includes("battery") || qLower.includes("apac")) {
    onAnswer({
      session_id: "demo_sess_1",
      run_id: "run_story1_demo",
      narrative: `### Executive Incident Report: APAC PearPhone 16 Pro Battery Claims Surge\n\n**Root Cause:** Component defect in battery cell lot **BP-2025-08** manufactured during June 2025.\n\n**Key Findings:**\n- **Claims Explosion:** In Q3 2025 (July–September), battery degradation claims in APAC spiked by **>3,000%**, exceeding 4,200 claims per month vs baseline ~120 claims.\n- **Hardware Concentration:** 100% of the anomalous battery failures trace directly to lot \`BP-2025-08\` on the PearPhone 16 Pro (\`PRD-PHN-16P\`).\n- **Warranty Cost Impact:** Total warranty claim costs exceeded $1.4M for the quarter.\n- **Resolution:** Supplier recall initiated on August 22, 2025; firmware thermal mitigation v18.0.2 deployed.`,
      visual_spec: {
        chart_type: "bar",
        x_axis: "month",
        series: ["battery_claims", "defective_lot_claims"],
        data: [
          { month: "May 2025", battery_claims: 131, defective_lot_claims: 0 },
          { month: "Jun 2025", battery_claims: 128, defective_lot_claims: 12 },
          { month: "Jul 2025", battery_claims: 4332, defective_lot_claims: 4210 },
          { month: "Aug 2025", battery_claims: 4337, defective_lot_claims: 4215 },
          { month: "Sep 2025", battery_claims: 4209, defective_lot_claims: 4095 },
          { month: "Oct 2025", battery_claims: 110, defective_lot_claims: 0 },
        ],
      },
      sql_query: `SELECT year, month, count(*) as battery_claims, count(case when component_batch_id = 'BP-2025-08' then 1 end) as defective_lot_claims FROM fact_support_claims WHERE region_id = 'APAC' AND claim_type LIKE '%Battery%' GROUP BY year, month ORDER BY year, month;`,
      data: [
        { month: "2025-07", battery_claims: 4332, defective_lot_claims: 4210, customer_name: role === "admin" ? "Samantha Wright" : "S***" },
        { month: "2025-08", battery_claims: 4337, defective_lot_claims: 4215, customer_name: role === "admin" ? "David Chen" : "D***" },
        { month: "2025-09", battery_claims: 4209, defective_lot_claims: 4095, customer_name: role === "admin" ? "Kenji Sato" : "K***" },
      ],
      citations: [
        { citation_id: "CIT-1", title: "2025-Q3 APAC Battery Degradation Postmortem", doc_type: "Postmortem", snippet: "Analysis of cell lot BP-2025-08 revealed separator film pinhole defects leading to accelerated impedance growth under tropical ambient temperatures.", score: 0.94 },
      ],
      governance: {
        status: "APPROVED",
        role,
        audit_id: "AUD-DEMO-001",
        violations: [],
      },
      steps,
    });
    return;
  }

  // Story 2
  if (qLower.includes("emea") || qLower.includes("marketing") || qLower.includes("retail")) {
    onAnswer({
      session_id: "demo_sess_2",
      run_id: "run_story2_demo",
      narrative: `### Executive Briefing: EMEA Q2 2025 Marketing Reduction & Retail Revenue Slump\n\n**Root Cause:** Discretionary 55% reduction in regional brand and digital marketing budget during Q2 2025.\n\n**Key Findings:**\n- **Marketing Contraction:** Average monthly marketing spend in EMEA plummeted from ~$450k in Q1 to under **$200k/month** in April, May, and June 2025.\n- **Direct Footfall Impact:** Retail store net revenue experienced a direct contraction of **~28% YoY**, while online channels remained relatively resilient (-6%).\n- **Attribution:** Driver waterfall analysis confirms marketing spend reduction was responsible for 72% of the retail revenue variance.`,
      visual_spec: {
        chart_type: "line",
        x_axis: "month",
        series: ["marketing_spend_k", "retail_revenue_m"],
        data: [
          { month: "Jan", marketing_spend_k: 450, retail_revenue_m: 8.2 },
          { month: "Feb", marketing_spend_k: 440, retail_revenue_m: 8.0 },
          { month: "Mar", marketing_spend_k: 460, retail_revenue_m: 8.4 },
          { month: "Apr (Slump)", marketing_spend_k: 190, retail_revenue_m: 5.9 },
          { month: "May (Slump)", marketing_spend_k: 185, retail_revenue_m: 5.7 },
          { month: "Jun (Slump)", marketing_spend_k: 195, retail_revenue_m: 6.0 },
          { month: "Jul (Rebound)", marketing_spend_k: 470, retail_revenue_m: 8.3 },
        ],
      },
      sql_query: `SELECT month, sum(spend_usd)/1000 as marketing_spend_k FROM fact_marketing_spend WHERE region_id = 'EMEA' AND year = 2025 GROUP BY month ORDER BY month;`,
      data: [
        { period: "Q1_baseline", avg_monthly_spend: "$450,000", avg_monthly_rev: "$8,200,000" },
        { period: "Q2_slump", avg_monthly_spend: "$190,000", avg_monthly_rev: "$5,860,000" },
      ],
      citations: [
        { citation_id: "CIT-1", title: "2025-Q2 EMEA Marketing Budget Variance Analysis", doc_type: "Finance Brief", snippet: "Q2 marketing reallocation into R&D created unexpected demand softness across physical retail footprint in UK and Germany.", score: 0.91 },
      ],
      governance: { status: "APPROVED", role, audit_id: "AUD-DEMO-002", violations: [] },
      steps,
    });
    return;
  }

  // Story 3
  if (qLower.includes("attach") || qLower.includes("watch") || qLower.includes("amer")) {
    onAnswer({
      session_id: "demo_sess_3",
      run_id: "run_story3_demo",
      narrative: `### Executive Briefing: AMER Q4 Holiday Wearables Attach Ratio Surge\n\n**Strategic Driver:** PearWatch Ultra 2 holiday bundle promotion and carrier cellular activations.\n\n**Key Findings:**\n- **Attach Ratio Surge:** During Q4 2025 (Oct–Dec), the attach ratio of PearWatch Ultra 2 (\`PRD-WCH-ULT2\`) to PearPhone 16 Pro (\`PRD-PHN-16P\`) rose to **0.372**, compared to an off-season baseline of 0.165.\n- **Volume Expansion:** PearWatch Ultra shipments exceeded 185,000 units in AMER during the holiday quarter alone.`,
      visual_spec: {
        chart_type: "bar",
        x_axis: "period",
        series: ["attach_ratio"],
        data: [
          { period: "Q1 2025", attach_ratio: 0.162 },
          { period: "Q2 2025", attach_ratio: 0.158 },
          { period: "Q3 2025", attach_ratio: 0.174 },
          { period: "Q4 Holiday 2025", attach_ratio: 0.372 },
        ],
      },
      sql_query: `SELECT case when month in (10, 11, 12) then 'Q4_holiday' else 'Non_Q4' end as period, sum(case when product_id = 'PRD-WCH-ULT2' then units else 0 end)*1.0 / sum(case when product_id = 'PRD-PHN-16P' then units else 0 end) as attach_ratio FROM fact_sales WHERE region_id = 'AMER' AND year = 2025 GROUP BY 1;`,
      data: [
        { period: "Non_Q4", attach_ratio: 0.165, watch_units: 92400, phone_units: 560000 },
        { period: "Q4_holiday", attach_ratio: 0.372, watch_units: 186000, phone_units: 500000 },
      ],
      citations: [
        { citation_id: "CIT-1", title: "Wearables GTM Holiday Attach Strategy", doc_type: "Strategy Doc", snippet: "Direct-to-consumer trade-in incentives for PearPhone upgrades bundled with 3 months free OrchardFitness+ drove unprecedented watch attach.", score: 0.89 },
      ],
      governance: { status: "APPROVED", role, audit_id: "AUD-DEMO-003", violations: [] },
      steps,
    });
    return;
  }

  // Story 4 or generic
  onAnswer({
    session_id: "demo_sess_4",
    run_id: "run_story4_demo",
    narrative: `### Engineering Postmortem: PearBook Pro 16" Display Flicker Defect Returns\n\n**Root Cause:** Display timing controller timing regression introduced in firmware update **v14.2**.\n\n**Key Findings:**\n- **Return Rate Anomaly:** Defective hardware return rates for PearBook Pro 16\" (\`PRD-NBK-16P\`) spiked to **5.1% in January 2025** and **4.9% in February 2025**, vs normal baseline of 2.1%.\n- **Primary Complaint:** Customer tickets cited screen blackout and 120Hz refresh flickering under GPU loads.\n- **Resolution:** Hotfix firmware **v14.2.1** released on Feb 24, 2025; returns normalized to 2.2% by April.`,
    visual_spec: {
      chart_type: "line",
      x_axis: "month",
      series: ["defect_return_rate"],
      data: [
        { month: "Jan 2025", defect_return_rate: 5.12 },
        { month: "Feb 2025", defect_return_rate: 4.88 },
        { month: "Mar 2025", defect_return_rate: 3.10 },
        { month: "Apr 2025", defect_return_rate: 2.24 },
        { month: "May 2025", defect_return_rate: 2.15 },
      ],
    },
    sql_query: `SELECT cast(s.month as integer) as month, count(distinct r.return_id)*100.0 / count(distinct s.sale_id) as defect_return_rate FROM fact_sales s LEFT JOIN fact_returns r ON s.sale_id = r.sale_id AND r.return_reason = 'Defective / Hardware Issue' WHERE s.product_id = 'PRD-NBK-16P' AND s.year = 2025 GROUP BY 1 ORDER BY 1;`,
    data: [
      { month: 1, sales_count: 14200, defective_returns: 727, defect_return_rate: "5.12%" },
      { month: 2, sales_count: 13800, defective_returns: 673, defect_return_rate: "4.88%" },
      { month: 4, sales_count: 14500, defective_returns: 325, defect_return_rate: "2.24%" },
    ],
    citations: [
      { citation_id: "CIT-1", title: "PearBook Display Firmware Regression v14.2", doc_type: "Postmortem", snippet: "Variable refresh rate synchronization glitch caused panel driver IC timing fault under external display connectivity.", score: 0.95 },
    ],
    governance: { status: "APPROVED", role, audit_id: "AUD-DEMO-004", violations: [] },
    steps,
  });
}
