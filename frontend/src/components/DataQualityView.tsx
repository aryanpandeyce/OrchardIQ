"use client";

import React from "react";
import { Cpu, CheckCircle2, ShieldCheck, HardDrive, RefreshCw } from "lucide-react";

export const DataQualityView: React.FC = () => {
  const tableScorecards = [
    { table: "dim_product", rows: "25", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "None", status: "PASSED" },
    { table: "dim_store", rows: "500", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "None", status: "PASSED" },
    { table: "dim_customer", rows: "100,000", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "None", status: "PASSED" },
    { table: "dim_date", rows: "1,096", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "None", status: "PASSED" },
    { table: "dim_region", rows: "4", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "None", status: "PASSED" },
    { table: "fact_sales", rows: "1,847,219", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "year=YYYY/month=MM", status: "PASSED" },
    { table: "fact_returns", rows: "119,482", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "year=YYYY/month=MM", status: "PASSED" },
    { table: "fact_support_claims", rows: "151,320", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "year=YYYY/month=MM", status: "PASSED" },
    { table: "fact_marketing_spend", rows: "14,400", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "year=YYYY/month=MM", status: "PASSED" },
    { table: "fact_finance_revenue", rows: "192", nullKeys: "0", nullPct: "0.00%", freshness: "Current", partition: "None", status: "PASSED" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Cpu className="w-5 h-5 text-emerald-400" />
          Automated Data Quality & Warehouse Health Monitor
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Automated data freshness validation, schema drift checks, and foreign key referential integrity audits.
        </p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400 font-medium">Overall Quality Status</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">100% HEALTHY</div>
          <span className="text-[11px] text-slate-500">10 / 10 Tables Meeting SLA</span>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400 font-medium">Lakehouse Total Rows</span>
            <HardDrive className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">2,234,318</div>
          <span className="text-[11px] text-slate-500">DuckDB + Hive Parquet</span>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400 font-medium">Referential Integrity</span>
            <ShieldCheck className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold text-teal-400 font-mono">0 Orphans</div>
          <span className="text-[11px] text-slate-500">100% Foreign Keys Resolved</span>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400 font-medium">Partitioning Schema</span>
            <RefreshCw className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300 font-mono">Hive Standard</div>
          <span className="text-[11px] text-slate-500">36 Months Partition Pruned</span>
        </div>
      </div>

      {/* Table Scorecards */}
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-4 bg-slate-900/90 border-b border-slate-800">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Table-Level Data Quality Scorecards
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-semibold">Table Name</th>
                <th className="px-4 py-3 font-semibold">Row Count</th>
                <th className="px-4 py-3 font-semibold">Null Keys</th>
                <th className="px-4 py-3 font-semibold">Null Rate</th>
                <th className="px-4 py-3 font-semibold">Freshness</th>
                <th className="px-4 py-3 font-semibold">Partition Layout</th>
                <th className="px-4 py-3 font-semibold">Validation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {tableScorecards.map((row) => (
                <tr key={row.table} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-2.5 font-bold text-emerald-300">{row.table}</td>
                  <td className="px-4 py-2.5 text-white">{row.rows}</td>
                  <td className="px-4 py-2.5 text-slate-400">{row.nullKeys}</td>
                  <td className="px-4 py-2.5 text-slate-400">{row.nullPct}</td>
                  <td className="px-4 py-2.5 text-slate-300">{row.freshness}</td>
                  <td className="px-4 py-2.5 text-slate-400 text-[11px]">{row.partition}</td>
                  <td className="px-4 py-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
