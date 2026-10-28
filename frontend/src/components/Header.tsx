"use client";

import React, { useState } from "react";
import { Shield, Database, BarChart3, Cpu, Radio, Sparkles, Zap, Key, X, Check } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeRole: string;
  setActiveRole: (role: string) => void;
  isLiveClaude: boolean;
  setIsLiveClaude: (live: boolean) => void;
  anthropicApiKey: string;
  setAnthropicApiKey: (key: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  activeRole,
  setActiveRole,
  isLiveClaude,
  setIsLiveClaude,
  anthropicApiKey,
  setAnthropicApiKey,
}) => {
  const [showKeyModal, setShowKeyModal] = useState<boolean>(false);
  const [tempKey, setTempKey] = useState<string>(anthropicApiKey);

  const handleToggleLiveClaude = () => {
    if (!isLiveClaude) {
      if (!anthropicApiKey) {
        setShowKeyModal(true);
      } else {
        setIsLiveClaude(true);
      }
    } else {
      setIsLiveClaude(false);
    }
  };

  const handleSaveKey = () => {
    setAnthropicApiKey(tempKey.trim());
    if (tempKey.trim()) {
      setIsLiveClaude(true);
    }
    setShowKeyModal(false);
  };

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

        {/* Controls: Mode Toggle & Role Switcher */}
        <div className="flex items-center gap-3">
          {/* Live Claude Toggle */}
          <div className="flex items-center bg-slate-900/90 rounded-lg p-0.5 border border-slate-800 text-xs">
            <button
              onClick={() => setIsLiveClaude(false)}
              className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                !isLiveClaude
                  ? "bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-300"
              }`}
              title="Demo Mode: High-fidelity deterministic multi-agent execution"
            >
              <span className={`w-1.5 h-1.5 rounded-full ${!isLiveClaude ? "bg-emerald-400 animate-pulse" : "bg-slate-500"}`}></span>
              <span>Demo Mode</span>
            </button>
            <button
              onClick={handleToggleLiveClaude}
              className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                isLiveClaude
                  ? "bg-purple-600/30 text-purple-200 font-semibold border border-purple-500/40"
                  : "text-slate-400 hover:text-slate-300"
              }`}
              title="Live Claude 3.5 Sonnet: Requires Anthropic API Key"
            >
              <Zap className={`w-3 h-3 ${isLiveClaude ? "text-purple-400" : "text-slate-500"}`} />
              <span>Live Claude</span>
              {anthropicApiKey ? (
                <span className="text-[9px] px-1 py-0.2 rounded bg-purple-500/20 text-purple-300 font-mono">Key Active</span>
              ) : (
                <Key
                  className="w-2.5 h-2.5 text-slate-500 hover:text-purple-400 cursor-pointer"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowKeyModal(true);
                  }}
                />
              )}
            </button>
          </div>

          {/* Role Switcher (Live RBAC PII Masking) */}
          <div className="flex items-center gap-1.5">
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
      </div>

      {/* Anthropic API Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Key className="w-4 h-4" />
                </div>
                <h3 className="font-semibold text-white">Live Claude 3.5 API Key</h3>
              </div>
              <button
                onClick={() => setShowKeyModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              OrchardIQ runs in <strong>Demo Mode</strong> by default. To enable live Claude 3.5 Sonnet reasoning with self-correction, enter your Anthropic API key below. Keys are stored only in your browser session.
            </p>

            <div className="space-y-1.5">
              <label className="text-[11px] font-medium text-slate-400">Anthropic API Key</label>
              <input
                type="password"
                value={tempKey}
                onChange={(e) => setTempKey(e.target.value)}
                placeholder="sk-ant-api03-..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 text-sm font-mono text-white placeholder-slate-600 outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveKey}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30 transition-all flex items-center gap-1.5"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Save & Enable</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

