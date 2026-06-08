export type PhaseStatus = "pending" | "running" | "completed" | "skipped" | "error";
export type Language = "uz" | "ru" | "en";
export type PhaseName = "router" | "opportunity" | "market_research" | "logistics" | "trade_engine" | "profit" | "decision";

export interface PhaseData {
  status: PhaseStatus;
  progress: number;
  ui_label?: string;
  details?: any;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface QueryRequest {
  product: string;
  language: Language;
  destination?: string;
  max_results?: number;
  use_cache?: boolean;
}

export interface QueryResponse {
  success: boolean;
  task_id: string;
  status: "processing" | "completed" | "error";
  flow?: string;
  phases?: Record<string, PhaseData>;
  result?: any;
  error?: string;
  timestamp: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  phases?: Record<string, PhaseData>;
  result?: any;
  timestamp: Date;
}

export const PHASE_LABELS: Record<string, { icon: string; label_uz: string; label_ru: string; label_en: string }> = {
  opportunity: {
    icon: "🔍",
    label_uz: "Bozorni o'rganish",
    label_ru: "Анализ рынка",
    label_en: "Market Research",
  },
  market_research: {
    icon: "📦",
    label_uz: "Narxlarni yig'ish",
    label_ru: "Сбор цен",
    label_en: "Price Collection",
  },
  logistics: {
    icon: "🚚",
    label_uz: "Narxlarni yig'ish",
    label_ru: "Сбор цен",
    label_en: "Price Collection",
  },
  trade_engine: {
    icon: "📊",
    label_uz: "Narxlarni yig'ish",
    label_ru: "Сбор цен",
    label_en: "Price Collection",
  },
  profit: {
    icon: "💰",
    label_uz: "Foyda hisoblash",
    label_ru: "Расчет прибыли",
    label_en: "Profit Calculation",
  },
  decision: {
    icon: "🧠",
    label_uz: "Tavsiya tayyorlash",
    label_ru: "Подготовка рекомендации",
    label_en: "Preparing Recommendation",
  },
};

export const UI_PHASES = [
  { key: "opportunity", label: "Bozorni o'rganish" },
  { key: "parallel", label: "Narxlarni yig'ish" },
  { key: "profit", label: "Foyda hisoblash" },
  { key: "decision", label: "Tavsiya tayyorlash" },
];

export function getPhaseIcon(key: string): string {
  return PHASE_LABELS[key]?.icon || "⚙️";
}

export function getPhaseLabel(key: string, lang: Language = "uz"): string {
  const labels = PHASE_LABELS[key];
  if (!labels) return key;
  return labels[`label_${lang}` as keyof typeof labels] as string || key;
}
