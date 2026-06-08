"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PhaseData, PhaseName, getPhaseIcon, getPhaseLabel, Language } from "@/lib/types";

interface AgentTimelineProps {
  phases: Record<string, PhaseData>;
  language?: Language;
}

const PHASE_ICONS: Record<string, string> = {
  opportunity: "🔍",
  market_research: "📦",
  logistics: "🚚",
  trade_engine: "📊",
  profit: "💰",
  decision: "🧠",
};

const PHASE_ORDER = ["opportunity", "market_research", "logistics", "trade_engine", "profit", "decision"];

function getStatusIcon(status: string): string {
  switch (status) {
    case "completed": return "✅";
    case "running": return "🔄";
    case "error": return "❌";
    case "skipped": return "⏭️";
    default: return "⏳";
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case "completed": return "border-success-400 bg-success-400/10";
    case "running": return "border-brand-400 bg-brand-400/10";
    case "error": return "border-error-400 bg-error-400/10";
    case "skipped": return "border-gray-600 bg-gray-800";
    default: return "border-gray-700 bg-gray-800/50";
  }
}

export function AgentTimeline({ phases, language = "uz" }: AgentTimelineProps) {
  const [expandedPhase, setExpandedPhase] = useState<string | null>(null);

  if (!phases || Object.keys(phases).length === 0) return null;

  const visiblePhases = PHASE_ORDER.filter((key) => phases[key]);
  const hasContent = visiblePhases.some((key) => key !== "router" && phases[key]?.status !== "pending");

  if (!hasContent) return null;

  return (
    <div className="space-y-1 my-4">
      <p className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-3">
        Agent Timeline
      </p>
      {visiblePhases.map((key, idx) => {
        const phase = phases[key];
        if (!phase || key === "router") return null;
        const isExpanded = expandedPhase === key;
        const isLast = idx === visiblePhases.filter((k) => k !== "router").length - 1;
        const statusColor = getStatusColor(phase.status);

        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="relative"
          >
            {!isLast && (
              <div className="absolute left-[17px] top-8 bottom-0 w-[2px] bg-gray-700" />
            )}
            <div
              className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-colors hover:bg-gray-800/50 ${statusColor}`}
              onClick={() => setExpandedPhase(isExpanded ? null : key)}
            >
              <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg bg-gray-800 shrink-0">
                {PHASE_ICONS[key] || "⚙️"}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-200">
                    {getPhaseLabel(key, language)}
                  </span>
                  <span className="text-xs">{getStatusIcon(phase.status)}</span>
                </div>
                <div className="mt-1.5 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${
                      phase.status === "completed" ? "bg-success-400" :
                      phase.status === "error" ? "bg-error-400" :
                      phase.status === "running" ? "bg-brand-400" : "bg-gray-600"
                    }`}
                    initial={{ width: "0%" }}
                    animate={{
                      width: phase.status === "completed" ? "100%" :
                             phase.status === "running" ? `${Math.max(phase.progress * 100, 20)}%` :
                             "0%",
                    }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                  />
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500 capitalize">{phase.status}</span>
                  {phase.status === "running" && (
                    <span className="text-xs text-gray-500">
                      {Math.round(phase.progress * 100)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
            <AnimatePresence>
              {isExpanded && phase.details && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="ml-12 mt-1 p-3 rounded-lg bg-gray-800/50 border border-gray-700/50"
                >
                  <pre className="text-xs text-gray-400 whitespace-pre-wrap overflow-x-auto max-h-40">
                    {JSON.stringify(phase.details, null, 2)}
                  </pre>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
    </div>
  );
}
