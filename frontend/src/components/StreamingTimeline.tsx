"use client";

import React from "react";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { StepLog } from "@/lib/api";

interface StreamingTimelineProps {
  steps: StepLog[];
  isStreaming: boolean;
}

export const StreamingTimeline: React.FC<StreamingTimelineProps> = ({ steps, isStreaming }) => {
  if (steps.length === 0 && !isStreaming) return null;

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-4 my-4">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          {isStreaming ? (
            <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          )}
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Multi-Agent Reasoning Timeline ({steps.length} Steps)
          </h3>
        </div>
        {isStreaming && (
          <span className="text-[11px] font-mono text-emerald-400 animate-pulse bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
            Graph Active
          </span>
        )}
      </div>

      <div className="space-y-2.5">
        {steps.map((step, idx) => {
          const isLatest = idx === steps.length - 1 && isStreaming;
          return (
            <div
              key={idx}
              className={`flex items-start gap-3 p-2.5 rounded-xl transition-all ${
                isLatest
                  ? "bg-slate-800/90 border border-emerald-500/40 shadow-sm"
                  : "bg-slate-950/40 border border-slate-800/60"
              }`}
            >
              <div className="mt-0.5">
                {step.status === "COMPLETED" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : step.status === "FAILED" ? (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                ) : (
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-0.5">
                  <span className="text-xs font-bold text-white tracking-wide">
                    {step.step_name}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {new Date(step.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {step.message}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
