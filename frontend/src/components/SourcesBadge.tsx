"use client";

interface SourcesBadgeProps {
  sources?: string[];
  opportunities?: any[];
  market?: { china_source?: string; uz_source?: string };
}

const SOURCE_META: Record<string, { icon: string; color: string }> = {
  Alibaba: { icon: "🅰️", color: "text-orange-400" },
  "1688": { icon: "🏭", color: "text-red-400" },
  "Made-in-China": { icon: "🇨🇳", color: "text-red-500" },
  Uzum: { icon: "🛒", color: "text-purple-400" },
  Olcha: { icon: "🛍️", color: "text-green-400" },
  Asaxiy: { icon: "📱", color: "text-blue-400" },
  Texnomart: { icon: "🔌", color: "text-yellow-400" },
  DB: { icon: "🗄️", color: "text-gray-400" },
  Web: { icon: "🌐", color: "text-sky-400" },
};

export function SourcesBadge({ sources, market, opportunities }: SourcesBadgeProps) {
  const sourceList: string[] = [];

  if (market?.china_source) {
    sourceList.push(market.china_source);
  }
  if (market?.uz_source) {
    sourceList.push(market.uz_source);
  }
  if (sources) {
    sourceList.push(...sources);
  }
  if (opportunities) {
    opportunities.forEach((o: any) => {
      if (o?.source) sourceList.push(o.source);
    });
  }

  if (sourceList.length === 0) return null;

  const unique = [...new Set(sourceList)].slice(0, 6);

  return (
    <div className="mt-4">
      <p className="text-xs text-gray-500 mb-2">Manbalar</p>
      <div className="flex flex-wrap gap-2">
        {unique.map((src) => {
          const meta = SOURCE_META[src];
          return (
            <span
              key={src}
              className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-gray-800 border border-gray-700 ${meta?.color || "text-gray-300"}`}
            >
              {meta?.icon || "📄"} {src}
            </span>
          );
        })}
      </div>
    </div>
  );
}
