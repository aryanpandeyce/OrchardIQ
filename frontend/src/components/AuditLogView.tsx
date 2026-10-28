"use client";

import React, { useState } from "react";
import { Shield, Filter } from "lucide-react";

export const AuditLogView: React.FC = () => {
  const [roleFilter, setRoleFilter] = useState("all");

  const sampleLogs = [
    { auditId: "AUD-89A4E2C7B102", time: "Just now", role: "analyst", question: "Why did warranty battery claims spike in APAC during Q3 2025?", decision: "MASKED", reason: "Restricted PII columns anonymized via SHA-256 tokens", latency: "382ms" },
    { auditId: "AUD-F489D018A451", time: "1m ago", role: "finance", question: "Explain marketing spend reduction and retail revenue slump in EMEA", decision: "APPROVED", reason: "Authorized finance scope validated by AST guardrails", latency: "408ms" },
    { auditId: "AUD-3B104F5E67A9", time: "3m ago", role: "analyst", question: "What caused the PearWatch Ultra attach ratio surge in AMER?", decision: "APPROVED", reason: "SELECT-only query validated with auto-LIMIT applied", latency: "394ms" },
    { auditId: "AUD-1A98BC34789F", time: "5m ago", role: "analyst", question: "PearBook Pro 16 display flicker defect return rates in Jan/Feb", decision: "APPROVED", reason: "Schema-grounded join between sales and returns allowed", latency: "432ms" },
    { auditId: "AUD-E99410A88753", time: "8m ago", role: "analyst", question: "DROP TABLE dim_customer; SELECT * FROM fact_sales", decision: "BLOCKED_UNSAFE_AST", reason: "Rejected destructive DDL mutation (DROP TABLE)", latency: "14ms" },
    { auditId: "AUD-71B044DF9021", time: "12m ago", role: "finance", question: "SELECT * FROM read_parquet('data/warehouse/dim_customer.parquet')", decision: "BLOCKED_FILE_READ", reason: "Direct file read bypassing lakehouse engine is forbidden", latency: "16ms" },
    { auditId: "AUD-0A481B983350", time: "15m ago", role: "analyst", question: "SELECT * FROM fact_finance_revenue", decision: "BLOCKED_TABLE_SCOPE", reason: "Role 'analyst' is not authorized to query fact_finance_revenue", latency: "19ms" },
  ];

  const filtered = sampleLogs.filter(
    (l) => roleFilter === "all" || l.role === roleFilter
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            Immutable Dual-Sided Governance Audit Log
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident record of all SQL AST security decisions, role-based table allowlists, and PII masking events.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
            {["all", "analyst", "finance", "admin"].map((r) => (
              <button
                key={r}
                onClick={() => setRoleFilter(r)}
                className={`px-3 py-1 rounded-lg capitalize transition-all ${
                  roleFilter === r
                    ? "bg-emerald-500 text-slate-950 font-bold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Recorded Governance Decisions ({filtered.length} Events)
          </h3>
          <span className="text-[11px] font-mono text-emerald-400">
            DuckDB Table: governance_audit_log
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-semibold">Audit ID</th>
                <th className="px-4 py-3 font-semibold">Time</th>
                <th className="px-4 py-3 font-semibold">Role</th>
                <th className="px-4 py-3 font-semibold">User Question</th>
                <th className="px-4 py-3 font-semibold">Governance Decision</th>
                <th className="px-4 py-3 font-semibold">Policy Enforcement Reason</th>
                <th className="px-4 py-3 font-semibold">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filtered.map((log) => {
                const isBlocked = log.decision.startsWith("BLOCKED");
                const isMasked = log.decision === "MASKED";
                return (
                  <tr key={log.auditId} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-2.5 font-bold text-slate-400">{log.auditId}</td>
                    <td className="px-4 py-2.5 text-slate-500">{log.time}</td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 text-[10px]">
                        {log.role}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-sans font-medium text-white max-w-xs truncate">
                      {log.question}
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isBlocked
                            ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            : isMasked
                            ? "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        }`}
                      >
                        {log.decision}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-sans text-slate-400 text-xs">
                      {log.reason}
                    </td>
                    <td className="px-4 py-2.5 text-slate-400">{log.latency}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
