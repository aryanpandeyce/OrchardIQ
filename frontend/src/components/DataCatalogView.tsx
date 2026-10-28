"use client";

import React, { useState } from "react";
import { Database, Search } from "lucide-react";

export const DataCatalogView: React.FC = () => {
  const [search, setSearch] = useState("");

  const tables = [
    {
      name: "dim_product",
      type: "Dimension",
      rows: "25 Products",
      desc: "Hardware product catalog (PearPhone, PearBook, PearWatch, PearPods, PearPad) with MSRP, BOM cost, and warranty terms.",
      cols: ["product_id", "product_name", "category", "product_line", "price_usd", "cost_usd", "warranty_months", "status"],
      security: "Public-Enterprise",
    },
    {
      name: "dim_customer",
      type: "Dimension",
      rows: "100,000 Customers",
      desc: "Customer demographic profile with Restricted PII (first_name, last_name, email, phone, street_address) masked for analysts.",
      cols: ["customer_id", "first_name", "last_name", "email", "phone", "street_address", "city", "country", "customer_segment"],
      security: "Restricted-PII (Masked)",
    },
    {
      name: "dim_store",
      type: "Dimension",
      rows: "500 Locations",
      desc: "Physical flagship retail stores and direct online fulfillment channels across worldwide operating regions.",
      cols: ["store_id", "store_name", "channel", "city", "state_province", "country", "region_id", "square_feet"],
      security: "Public-Enterprise",
    },
    {
      name: "dim_date",
      type: "Dimension",
      rows: "1,096 Calendar Days",
      desc: "Fiscal calendar table with Orchard 4-4-5 accounting periods, holidays, and fiscal quarter mappings.",
      cols: ["date_id", "full_date", "day_name", "month_name", "fiscal_quarter", "fiscal_year", "is_weekend"],
      security: "Public-Enterprise",
    },
    {
      name: "fact_sales",
      type: "Transactional Fact",
      rows: "~1,850,000 Transactions",
      desc: "Granular hardware sales and order lines partitioned by Hive year=YYYY/month=MM with revenue and gross margin metrics.",
      cols: ["sale_id", "date_id", "customer_id", "product_id", "store_id", "region_id", "units", "gross_revenue", "net_revenue", "gross_margin"],
      security: "Public-Enterprise",
    },
    {
      name: "fact_returns",
      type: "Transactional Fact",
      rows: "~120,000 Returns",
      desc: "Product return logs linked to sales orders with defect codes (e.g. firmware flicker regression v14.2) and refund amounts.",
      cols: ["return_id", "sale_id", "date_id", "product_id", "return_reason", "units", "refund_amount", "restock_status"],
      security: "Public-Enterprise",
    },
    {
      name: "fact_support_claims",
      type: "Transactional Fact",
      rows: "~150,000 Claims",
      desc: "OrchardCare+ warranty claims tracking hardware failures, thermal incidents, turnaround days, and component lot tracing (e.g. BP-2025-08).",
      cols: ["claim_id", "date_id", "product_id", "claim_type", "repair_cost", "turnaround_days", "component_batch_id"],
      security: "Public-Enterprise",
    },
    {
      name: "fact_marketing_spend",
      type: "Aggregated Fact",
      rows: "Daily Campaigns",
      desc: "Multi-channel regional marketing expenditures, ad impressions, conversion tracking, and CAC metrics.",
      cols: ["spend_id", "date_id", "region_id", "product_id", "channel", "spend_usd", "impressions", "clicks", "conversions"],
      security: "Public-Enterprise",
    },
    {
      name: "fact_finance_revenue",
      type: "GAAP Financial Fact",
      rows: "Quarterly GAAP",
      desc: "Recognized GAAP net revenue, deferred services revenue, and operating margin restricted to Finance and Admin roles.",
      cols: ["finance_entry_id", "fiscal_quarter", "fiscal_year", "region_id", "product_line", "recognized_net_revenue", "operating_margin"],
      security: "Restricted-Finance",
    },
  ];

  const filtered = tables.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.desc.toLowerCase().includes(search.toLowerCase()) ||
      t.cols.some((c) => c.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-400" />
            Enterprise Data Catalog & Star-Schema Warehouse
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Browse tables, physical partitioning keys, column schemas, and RBAC governance policies.
          </p>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tables, columns, or tags..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {filtered.map((t) => (
          <div
            key={t.name}
            className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-emerald-300">{t.name}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono border border-slate-700">
                  {t.type}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">{t.rows}</span>
              </div>

              <span
                className={`text-[10px] px-2.5 py-0.5 rounded-full font-mono font-semibold ${
                  t.security.includes("Restricted-PII")
                    ? "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                    : t.security.includes("Restricted-Finance")
                    ? "bg-rose-500/10 text-rose-300 border border-rose-500/30"
                    : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                }`}
              >
                {t.security}
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed mb-3">{t.desc}</p>

            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] font-semibold text-slate-500 mr-1">Columns:</span>
              {t.cols.map((col) => (
                <span
                  key={col}
                  className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-950/80 text-slate-400 border border-slate-800/80"
                >
                  {col}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
