"use client";

import { motion } from "framer-motion";

interface OpportunityData {
  product_name?: string;
  china_price_usd?: number;
  uz_price_usd?: number;
  total_landed_usd?: number;
  profit_usd?: number;
  margin_pct?: number;
  confidence?: { overall?: number };
}

interface OpportunityCardProps {
  data?: OpportunityData;
  title?: string;
  index?: number;
}

export function OpportunityCard({ data, title, index = 0 }: OpportunityCardProps) {
  if (!data) return null;

  const margin = data.margin_pct ?? 0;
  const confidence = data.confidence?.overall ?? 0;
  const profitColor = margin > 100 ? "text-success-400" : margin > 50 ? "text-warning-400" : "text-gray-400";
  const confidenceColor = confidence > 0.7 ? "bg-success-400" : confidence > 0.4 ? "bg-warning-400" : "bg-gray-500";

  const productName = data.product_name || title || "Mahsulot";
  const chinaPrice = data.china_price_usd;
  const uzPrice = data.uz_price_usd;
  const landedCost = data.total_landed_usd;
  const profit = data.profit_usd;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 hover:border-brand-500/50 transition-colors"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-200">{productName}</h3>
        {margin > 0 && (
          <span className={`text-lg font-bold ${profitColor}`}>
            +{margin}%
          </span>
        )}
      </div>

      {chinaPrice && (
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-500">China</span>
            <span className="text-gray-300">${chinaPrice.toFixed(2)}</span>
          </div>
          {landedCost && (
            <div className="flex justify-between">
              <span className="text-gray-500">Landed</span>
              <span className="text-gray-300">${landedCost.toFixed(2)}</span>
            </div>
          )}
          {uzPrice && (
            <div className="flex justify-between">
              <span className="text-gray-500">Uzbekistan</span>
              <span className="text-gray-300">${uzPrice.toFixed(2)}</span>
            </div>
          )}
          {profit && (
            <div className="flex justify-between border-t border-gray-700 pt-1.5 mt-1.5">
              <span className="text-gray-500">Foyda</span>
              <span className={`font-semibold ${profitColor}`}>${profit.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}

      {!chinaPrice && (
        <p className="text-xs text-gray-500">Ma'lumotlar yig'ilmoqda...</p>
      )}

      {confidence > 0 && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
            <span>Ishonchlilik</span>
            <span>{Math.round(confidence * 100)}%</span>
          </div>
          <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${confidenceColor}`}
              initial={{ width: 0 }}
              animate={{ width: `${confidence * 100}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
        </div>
      )}
    </motion.div>
  );
}
