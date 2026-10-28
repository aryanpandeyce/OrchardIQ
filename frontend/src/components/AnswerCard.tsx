"use client";

import React, { useState } from "react";
import {
  Shield,
  Code2,
  FileText,
  BarChart,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Table as TableIcon,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart as RechartsBar,
  Bar,
  LineChart as RechartsLine,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { AnswerPayload } from "@/lib/api";

interface AnswerCardProps {
  answer: AnswerPayload;
  activeRole: string;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ answer, activeRole }) => {
  const [copiedSql, setCopiedSql] = useState(false);
  const [showSql, setShowSql] = useState(true);
  const [showTable, setShowTable] = useState(true);

  const handleCopySql = () => {
    if (answer.sql_query) {
      navigator.clipboard.writeText(answer.sql_query);
      setCopiedSql(true);
      setTimeout(() => setCopiedSql(false), 2000);
    }
  };

  const chartSpec = answer.visual_spec;
  const tableData = answer.data || [];
  const tableCols = tableData.length > 0 ? Object.keys(tableData[0]) : [];

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl my-6 space-y-6 transition-all">
      {/* Governance & Status Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Governance Verified
            </span>
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-mono">
              <span>Status:</span>
              <span className="text-emerald-400 font-semibold">{answer.governance.status}</span>
              <span>•</span>
              <span>Role:</span>
              <span className="text-cyan-400 font-semibold">{answer.governance.role}</span>
              <span>•</span>
              <span>Audit:</span>
              <span className="text-slate-300 font-semibold">{answer.governance.audit_id || "AUD-VERIFIED"}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 font-mono border border-slate-700">
            DuckDB Star-Schema Lakehouse
          </span>
          {activeRole !== "admin" && (
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 font-mono border border-amber-500/30">
              PII Masked (SHA-256 Tokens)
            </span>
          )}
        </div>
      </div>

      {/* Plain-English Markdown Executive Narrative */}
      <div className="prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed space-y-3 font-sans">
        <div
          dangerouslySetInnerHTML={{
            __html: answer.narrative
              .replace(/### (.*)/g, '<h3 class="text-base font-bold text-white mb-2">$1</h3>')
              .replace(/\*\*(.*?)\*\*/g, '<strong class="text-emerald-300 font-semibold">$1</strong>')
              .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono text-xs">$1</code>')
              .replace(/- (.*)/g, '<li class="ml-4 list-disc text-slate-300 my-1">$1</li>')
              .replace(/\n\n/g, '<div class="my-2"></div>'),
          }}
        />
      </div>

      {/* Interactive Recharts Visualization */}
      {chartSpec && chartSpec.data && chartSpec.data.length > 0 && (
        <div className="bg-slate-950/60 border border-slate-800 rounded-2xl p-5 my-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BarChart className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Interactive Telemetry Visualization ({chartSpec.chart_type.toUpperCase()})
              </h4>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              X-Axis: {chartSpec.x_axis}
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              {chartSpec.chart_type === "bar" ? (
                <RechartsBar data={chartSpec.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
                  <XAxis dataKey={chartSpec.x_axis} stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "0.75rem",
                      color: "#f8fafc",
                      fontSize: "12px",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
                  {chartSpec.series.map((s, idx) => (
                    <Bar
                      key={s}
                      dataKey={s}
                      fill={idx === 0 ? "#10b981" : idx === 1 ? "#06b6d4" : "#f59e0b"}
                      radius={[4, 4, 0, 0]}
                    />
                  ))}
                </RechartsBar>
              ) : (
                <RechartsLine data={chartSpec.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
                  <XAxis dataKey={chartSpec.x_axis} stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "0.75rem",
                      color: "#f8fafc",
                      fontSize: "12px",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
                  {chartSpec.series.map((s, idx) => (
                    <Line
                      key={s}
                      type="monotone"
                      dataKey={s}
                      stroke={idx === 0 ? "#10b981" : idx === 1 ? "#f43f5e" : "#06b6d4"}
                      strokeWidth={2.5}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  ))}
                </RechartsLine>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Interactive Data Table with Highlighted PII Masking */}
      {tableData.length > 0 && (
        <div className="bg-slate-950/60 border border-slate-800 rounded-2xl overflow-hidden">
          <div
            className="flex items-center justify-between p-3.5 bg-slate-900/60 cursor-pointer select-none"
            onClick={() => setShowTable(!showTable)}
          >
            <div className="flex items-center gap-2">
              <TableIcon className="w-4 h-4 text-cyan-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Ground-Truth Fact Records ({tableData.length} Rows)
              </h4>
            </div>
            {showTable ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </div>

          {showTable && (
            <div className="overflow-x-auto max-h-60">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900 text-slate-400 uppercase tracking-wider text-[10px] sticky top-0 border-b border-slate-800">
                  <tr>
                    {tableCols.map((col) => (
                      <th key={col} className="px-4 py-2.5 font-semibold">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {tableData.map((row, i) => (
                    <tr key={i} className="hover:bg-slate-900/40 transition-colors">
                      {tableCols.map((col) => {
                        const val = String(row[col] ?? "");
                        const isMasked = val.startsWith("anon_") || val.includes("***");
                        return (
                          <td key={col} className="px-4 py-2 whitespace-nowrap">
                            {isMasked ? (
                              <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px]">
                                {val}
                              </span>
                            ) : (
                              <span>{val}</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Executed DuckDB SQL Inspector Accordion */}
      {answer.sql_query && (
        <div className="bg-slate-950/60 border border-slate-800 rounded-2xl overflow-hidden">
          <div
            className="flex items-center justify-between p-3.5 bg-slate-900/60 cursor-pointer select-none"
            onClick={() => setShowSql(!showSql)}
          >
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                DuckDB Executed SQL (Schema-Grounded)
              </h4>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleCopySql();
                }}
                className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-[11px] text-slate-300 transition-colors border border-slate-700"
              >
                {copiedSql ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copiedSql ? "Copied" : "Copy SQL"}</span>
              </button>
              {showSql ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
            </div>
          </div>

          {showSql && (
            <div className="p-4 bg-slate-950/90 font-mono text-xs text-emerald-400 overflow-x-auto leading-relaxed border-t border-slate-800/60">
              <pre>{answer.sql_query}</pre>
            </div>
          )}
        </div>
      )}

      {/* Knowledge Base Citations Drawer */}
      {answer.citations && answer.citations.length > 0 && (
        <div className="bg-slate-950/40 border border-slate-800/80 rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-4 h-4 text-teal-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Verified Source Citations ({answer.citations.length})
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {answer.citations.map((c, i) => (
              <div
                key={i}
                className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs hover:border-slate-700 transition-all"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-bold text-white truncate">{c.title}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-teal-500/10 text-teal-300 border border-teal-500/20">
                    {c.doc_type}
                  </span>
                </div>
                <p className="text-slate-400 text-[11px] line-clamp-2 italic">
                  &ldquo;{c.snippet}&rdquo;
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
