"use client";

import React from "react";
import { BatteryCharging, TrendingDown, Watch, Laptop, Sparkles } from "lucide-react";

interface DemoChipsProps {
  onSelectQuestion: (query: string) => void;
  isLoading: boolean;
}

export const DEMO_QUESTIONS = [
  {
    id: "story-1",
    tag: "Story 1 · Hardware Defect",
    title: "APAC Battery Claims Surge",
    query: "Why did warranty battery degradation claims spike for PearPhone 16 Pro in APAC during Q3 2025?",
    icon: BatteryCharging,
    accent: "from-amber-500/10 to-orange-500/10 border-amber-500/30 text-amber-400",
  },
  {
    id: "story-2",
    tag: "Story 2 · Strategy & Demand",
    title: "EMEA Retail Revenue Slump",
    query: "Explain the relationship between marketing spend reduction and retail revenue slump in EMEA during Q2 2025.",
    icon: TrendingDown,
    accent: "from-rose-500/10 to-red-500/10 border-rose-500/30 text-rose-400",
  },
  {
    id: "story-3",
    tag: "Story 3 · Ecosystem Attach",
    title: "AMER Wearables Attach Spike",
    query: "What caused the PearWatch Ultra attach ratio to surge in AMER during Q4 2025?",
    icon: Watch,
    accent: "from-emerald-500/10 to-teal-500/10 border-emerald-500/30 text-emerald-400",
  },
  {
    id: "story-4",
    tag: "Story 4 · Quality & Firmware",
    title: "PearBook Display Flicker Returns",
    query: "What caused the defect return rate spike for PearBook Pro 16 in January and February 2025?",
    icon: Laptop,
    accent: "from-cyan-500/10 to-blue-500/10 border-cyan-500/30 text-cyan-400",
  },
];

export const DemoChips: React.FC<DemoChipsProps> = ({ onSelectQuestion, isLoading }) => {
  return (
    <div className="w-full">
      <div className="flex items-center gap-2 mb-2.5">
        <Sparkles className="w-4 h-4 text-emerald-400" />
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Verified Ground-Truth Story Demos (Click to ask)
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {DEMO_QUESTIONS.map((q) => {
          const Icon = q.icon;
          return (
            <button
              key={q.id}
              disabled={isLoading}
              onClick={() => onSelectQuestion(q.query)}
              className={`text-left p-3.5 rounded-xl bg-slate-900/80 border hover:border-slate-600 transition-all duration-200 group relative overflow-hidden backdrop-blur-sm ${
                q.accent
              } ${isLoading ? "opacity-50 cursor-not-allowed" : "hover:-translate-y-0.5 hover:shadow-lg"}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-semibold opacity-80">
                  {q.tag}
                </span>
                <Icon className="w-4 h-4 opacity-90 group-hover:scale-110 transition-transform" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1 group-hover:text-emerald-300 transition-colors">
                {q.title}
              </h4>
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                {q.query}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
};
