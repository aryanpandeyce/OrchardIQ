"use client";

import React, { useState } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";
import { Header } from "@/components/Header";
import { DemoChips } from "@/components/DemoChips";
import { StreamingTimeline } from "@/components/StreamingTimeline";
import { AnswerCard } from "@/components/AnswerCard";
import { DataCatalogView } from "@/components/DataCatalogView";
import { EvalBenchmarkView } from "@/components/EvalBenchmarkView";
import { DataQualityView } from "@/components/DataQualityView";
import { AuditLogView } from "@/components/AuditLogView";
import { LiveStreamView } from "@/components/LiveStreamView";
import { askQuestionStream, StepLog, AnswerPayload } from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("chat");
  const [activeRole, setActiveRole] = useState<string>("analyst");
  const [isLiveClaude, setIsLiveClaude] = useState<boolean>(false);
  const [anthropicApiKey, setAnthropicApiKey] = useState<string>("");
  const [inputQuery, setInputQuery] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [steps, setSteps] = useState<StepLog[]>([]);
  const [currentAnswer, setCurrentAnswer] = useState<AnswerPayload | null>(null);

  const handleAsk = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || isLoading) return;

    setIsLoading(true);
    setSteps([]);
    setCurrentAnswer(null);

    await askQuestionStream(
      q,
      activeRole,
      (step) => {
        setSteps((prev) => {
          const existing = prev.findIndex((s) => s.step_name === step.step_name);
          if (existing >= 0) {
            const updated = [...prev];
            updated[existing] = step;
            return updated;
          }
          return [...prev, step];
        });
      },
      (answer) => {
        setCurrentAnswer(answer);
        setIsLoading(false);
      },
      (err) => {
        console.error("Ask error:", err);
        setIsLoading(false);
      },
      isLiveClaude,
      anthropicApiKey
    );
  };

  const handleSelectQuestion = (q: string) => {
    setInputQuery(q);
    handleAsk(q);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500/30 selection:text-emerald-200">
      {/* Navigation Header with Live Role Switcher & Live Claude Toggle */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeRole={activeRole}
        setActiveRole={setActiveRole}
        isLiveClaude={isLiveClaude}
        setIsLiveClaude={setIsLiveClaude}
        anthropicApiKey={anthropicApiKey}
        setAnthropicApiKey={setAnthropicApiKey}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {activeTab === "chat" && (
          <div className="space-y-6 max-w-5xl mx-auto">
            {/* Workspace Hero Header */}
            <div className="text-center py-4 space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300 font-medium">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>Multi-Agent LangGraph • DuckDB Lakehouse • Dual-Sided Governance</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
                Ask OrchardIQ Anything
              </h1>
              <p className="text-sm text-slate-400 max-w-2xl mx-auto leading-relaxed">
                Autonomous reasoning over 2.2M+ transactional fact records and 31 knowledge base engineering documents.
                Governed by strict AST policies and real-time RBAC masking.
              </p>
            </div>

            {/* Clickable Ground-Truth Demo Story Chips */}
            <DemoChips onSelectQuestion={handleSelectQuestion} isLoading={isLoading} />

            {/* Natural Language Query Input Form */}
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-2.5 shadow-2xl focus-within:border-emerald-500/50 transition-all">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleAsk();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder={`Ask in natural language as '${activeRole}' (e.g. 'Why did battery claims spike in APAC during Q3 2025?')...`}
                  className="flex-1 bg-transparent px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !inputQuery.trim()}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 text-slate-950 font-bold text-xs flex items-center gap-2 transition-all shadow-md shadow-emerald-500/20 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Reasoning...</span>
                    </>
                  ) : (
                    <>
                      <span>Execute</span>
                      <Send className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Real-time Streaming Multi-Agent Timeline */}
            <StreamingTimeline steps={steps} isStreaming={isLoading} />

            {/* Comprehensive Answer Card */}
            {currentAnswer && (
              <AnswerCard answer={currentAnswer} activeRole={activeRole} />
            )}

            {/* Initial Empty State Placeholder if no query executed yet */}
            {!isLoading && !currentAnswer && (
              <div className="text-center py-12 px-4 border border-dashed border-slate-800/80 rounded-3xl bg-slate-900/20">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <Sparkles className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-white mb-1">
                  Ready for Executive Inquiries
                </h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Click any of the 4 verified story chips above or type a custom question to watch the agent graph plan, query DuckDB, enforce governance, and synthesize answers.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Dedicated Views */}
        {activeTab === "catalog" && <DataCatalogView />}
        {activeTab === "evals" && <EvalBenchmarkView />}
        {activeTab === "quality" && <DataQualityView />}
        {activeTab === "audit" && <AuditLogView />}
        {activeTab === "stream" && <LiveStreamView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 px-6 py-4 text-xs text-slate-500 text-center">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-2">
          <span>OrchardIQ Platform • Enterprise GenAI & Data Lakehouse Architecture</span>
          <span className="font-mono text-[11px] text-slate-400">
            Tech Stack: Next.js 15 • DuckDB • LangGraph • PyTorch • FastAPI • ChromaDB
          </span>
        </div>
      </footer>
    </div>
  );
}
