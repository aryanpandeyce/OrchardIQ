"use client";

import React, { useState, useEffect } from "react";
import { Radio, Activity } from "lucide-react";

interface StreamEvent {
  id: string;
  timestamp: string;
  eventType: "SALE" | "CLAIM" | "RETURN" | "ATTACH";
  product: string;
  region: string;
  amount: string;
  badgeColor: string;
}

export const LiveStreamView: React.FC = () => {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [throughput, setThroughput] = useState(24.5);

  useEffect(() => {
    const products = ["PearPhone 16 Pro", "PearBook Pro 16", "PearWatch Ultra 2", "PearPods Max", "PearPad Air"];
    const regions = ["AMER", "EMEA", "APAC", "LATAM"];
    const types: ("SALE" | "CLAIM" | "RETURN" | "ATTACH")[] = ["SALE", "CLAIM", "RETURN", "ATTACH"];

    const interval = setInterval(() => {
      const type = types[Math.floor(Math.random() * types.length)];
      const prod = products[Math.floor(Math.random() * products.length)];
      const reg = regions[Math.floor(Math.random() * regions.length)];
      const amount = type === "SALE" ? `$${(Math.random() * 1200 + 499).toFixed(0)}` : type === "CLAIM" ? `$${(Math.random() * 250 + 79).toFixed(0)}` : `$${(Math.random() * 800 + 199).toFixed(0)}`;

      const newEvent: StreamEvent = {
        id: `EVT-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
        timestamp: new Date().toLocaleTimeString(),
        eventType: type,
        product: prod,
        region: reg,
        amount,
        badgeColor:
          type === "SALE"
            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
            : type === "CLAIM"
            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
            : type === "ATTACH"
            ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
            : "bg-amber-500/10 text-amber-400 border-amber-500/30",
      };

      setEvents((prev) => [newEvent, ...prev.slice(0, 19)]);
      setThroughput(+(24 + Math.random() * 4 - 2).toFixed(1));
    }, 1200);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Radio className="w-5 h-5 text-emerald-400 animate-pulse" />
            Near-Real-Time Lakehouse Ingestion Stream
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Simulated event stream feeding transactional telemetry into the staging buffer and live analytics tiles.
          </p>
        </div>

        <div className="flex items-center gap-4 bg-slate-900 border border-slate-800 rounded-2xl px-4 py-2">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
            <span className="text-xs font-bold text-white font-mono">{throughput} msg/sec</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-xs text-slate-400 font-medium">Kafka / Microbatch Staging Buffer</span>
        </div>
      </div>

      {/* Stream Table */}
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            Live Ingestion Stream Ticker (Latest 20 Events)
          </h3>
          <span className="text-[11px] font-mono text-cyan-400">Buffer: Active</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-semibold">Event ID</th>
                <th className="px-4 py-3 font-semibold">Time</th>
                <th className="px-4 py-3 font-semibold">Type</th>
                <th className="px-4 py-3 font-semibold">Product Entity</th>
                <th className="px-4 py-3 font-semibold">Region</th>
                <th className="px-4 py-3 font-semibold">Value</th>
                <th className="px-4 py-3 font-semibold">Sink Destination</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {events.map((e) => (
                <tr key={e.id} className="hover:bg-slate-800/40 transition-colors animate-fadeIn">
                  <td className="px-4 py-2 font-bold text-slate-400">{e.id}</td>
                  <td className="px-4 py-2 text-slate-500">{e.timestamp}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${e.badgeColor}`}>
                      {e.eventType}
                    </span>
                  </td>
                  <td className="px-4 py-2 font-sans font-medium text-white">{e.product}</td>
                  <td className="px-4 py-2 text-slate-300">{e.region}</td>
                  <td className="px-4 py-2 text-emerald-400 font-semibold">{e.amount}</td>
                  <td className="px-4 py-2 text-slate-500 text-[11px]">fact_{e.eventType.toLowerCase()}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
