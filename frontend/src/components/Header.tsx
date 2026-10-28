"use client";

import React from "react";
import { Shield, Database, BarChart3, Cpu, Radio, Sparkles } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeRole: string;
  setActiveRole: (role: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  activeRole,
  setActiveRole,
}) => {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-slate-950/80 border-b border-slate-800/80 px-6 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand Logo & Tagline */}
        <div className="flex items-center gap-3.5 cursor-pointer" onClick={() => setActiveTab("chat")}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-400 to-cyan-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 ring-1 ring-emerald-400/30">
            <span className="text-xl font-black text-slate-950">🍏</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                OrchardIQ
              </span>
              <span className="text-[10px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                v0.1.0 MVP
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Agentic Enterprise Analytics & Lakehouse Intelligence</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800/80 text-xs font-medium">
          {[
            { id: "chat", label: "Analytics Workspace", icon: Sparkles },
            { id: "catalog", label: "Data Catalog", icon: Database },
            { id: "evals", label: "Eval Benchmark", icon: BarChart3 },
            { id: "quality", label: "Data Quality", icon: Cpu },
            { id: "audit", label: "Governance Audit", icon: Shield },
            { id: "stream", label: "Live Ticker", icon: Radio },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  isActive
                    ? "bg-emerald-500 text-slate-950 font-semibold shadow-md shadow-emerald-500/20"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Role Switcher (Demonstrating Live RBAC PII Masking) */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
            <Shield className="w-3.5 h-3.5 text-cyan-400" />
            Active Role:
          </span>
          <div className="flex items-center bg-slate-900/90 rounded-lg p-0.5 border border-slate-800 text-xs">
            {[
              { id: "analyst", label: "Analyst", badge: "PII Masked" },
              { id: "finance", label: "Finance", badge: "No PII" },
              { id: "admin", label: "Admin", badge: "Full Access" },
            ].map((r) => {
              const isSelected = activeRole === r.id;
              return (
                <button
                  key={r.id}
                  onClick={() => setActiveRole(r.id)}
                  className={`px-2.5 py-1 rounded-md transition-all text-xs flex items-center gap-1.5 ${
                    isSelected
                      ? "bg-slate-800 text-white font-semibold shadow-sm border border-slate-700"
                      : "text-slate-400 hover:text-slate-300"
                  }`}
                  title={`Switch to ${r.label} role (${r.badge})`}
                >
                  <span>{r.label}</span>
                  <span
                    className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                      isSelected
                        ? r.id === "admin"
                          ? "bg-rose-500/20 text-rose-300"
                          : r.id === "finance"
                          ? "bg-amber-500/20 text-amber-300"
                          : "bg-cyan-500/20 text-cyan-300"
                        : "text-slate-500"
                    }`}
                  >
                    {r.badge}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </header>
  );
};
