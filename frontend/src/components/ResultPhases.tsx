"use client";

import { PhaseData, QueryResponse } from "@/lib/types";

interface ResultPhasesProps {
  response: QueryResponse;
}

export function ResultPhases({ response }: ResultPhasesProps) {
  if (!response.phases) return null;

  const phases = response.phases;
  const discovery = phases.opportunity?.details;
  const analyst = phases.trade_engine?.details;
  const decision = phases.decision?.details;

  return (
    <div className="space-y-6 mt-8 w-full max-w-3xl mx-auto">
      {discovery && discovery.sources && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-blue-900 mb-4">
            1. Narxlar ({(discovery as any).total_sources || discovery.sources.length} manbadan)
          </h2>
          <div className="space-y-3">
            {(discovery.sources as any[]).map((source: any, idx: number) => (
              <div key={idx} className="bg-white p-4 rounded border border-blue-100 flex justify-between items-start">
                <div>
                  <p className="font-semibold">{(source.source || "").toUpperCase()}</p>
                  <p className="text-gray-600 text-sm">{source.product_name}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Ishonchlilik: {((source.confidence || 0) * 100).toFixed(0)}%
                  </p>
                  {source.source_url && (
                    <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 text-xs hover:underline">Manba</a>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-green-600">${(source.price || 0).toFixed(2)}</p>
                  <p className="text-xs text-gray-500">{source.currency || "USD"}</p>
                </div>
              </div>
            ))}
          </div>
          {(discovery as any).average_price_usd != null && (
            <div className="mt-4 bg-white p-4 rounded border-l-4 border-blue-500">
              <p className="text-gray-700">
                <strong>O'rtacha:</strong>{" "}
                <span className="text-xl font-bold text-blue-600">${(discovery as any).average_price_usd.toFixed(2)}</span>
              </p>
            </div>
          )}
        </div>
      )}
      {analysisView(analyst)}
      {decisionView(decision)}
      {fallbackView(response)}
    </div>
  );
}

function analysisView(analyst: any) {
  if (!analyst || !analyst.hs_code) return null;
  return (
    <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
      <h2 className="text-xl font-bold text-orange-900 mb-4">2. Import Tahlili</h2>
      <div className="grid grid-cols-2 gap-4 mb-4">
        {analyst.hs_code && (
          <div className="bg-white p-4 rounded border border-orange-100">
            <p className="text-gray-600 text-xs">HS Kod</p>
            <p className="text-xl font-bold">{analyst.hs_code}</p>
            {analyst.hs_description && <p className="text-xs text-gray-500">{analyst.hs_description}</p>}
          </div>
        )}
        {analyst.duty_pct != null && (
          <div className="bg-white p-4 rounded border border-orange-100">
            <p className="text-gray-600 text-xs">Boj</p>
            <p className="text-xl font-bold text-orange-600">{analyst.duty_pct}%</p>
          </div>
        )}
        {analyst.vat_pct != null && (
          <div className="bg-white p-4 rounded border border-orange-100">
            <p className="text-gray-600 text-xs">QQS (VAT)</p>
            <p className="text-xl font-bold text-orange-600">{analyst.vat_pct}%</p>
          </div>
        )}
        {analyst.freight_pct != null && (
          <div className="bg-white p-4 rounded border border-orange-100">
            <p className="text-gray-600 text-xs">Yuk</p>
            <p className="text-xl font-bold">${analyst.freight_pct}%</p>
          </div>
        )}
      </div>
    </div>
  );
}

function decisionView(decision: any) {
  if (!decision || !decision.breakdown) return null;
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-6">
      <h2 className="text-xl font-bold text-green-900 mb-4">3. Yakuniy Hisob</h2>
      <div className="bg-white p-6 rounded border-2 border-green-200 mb-4 space-y-3">
        {[
          { label: "Mahsulot", value: decision.breakdown.product, color: "" },
          { label: "Boj", value: decision.breakdown.duty, color: "text-orange-600" },
          { label: "QQS", value: decision.breakdown.vat, color: "text-orange-600" },
          { label: "Yuk", value: decision.breakdown.freight, color: "text-orange-600" },
        ].map((item: any) => (
          <div key={item.label} className="flex justify-between text-lg">
            <span>{item.label}</span>
            <span className={`font-semibold ${item.color}`}>${(item.value || 0).toFixed(2)}</span>
          </div>
        ))}
        {decision.total_landed_cost_usd != null && (
          <>
            <div className="border-t-2 pt-3 flex justify-between text-xl">
              <span className="font-bold">Jami (USD)</span>
              <span className="font-bold text-green-600 text-2xl">${decision.total_landed_cost_usd.toFixed(2)}</span>
            </div>
            {decision.total_landed_cost_uzs != null && (
              <div className="flex justify-between text-lg">
                <span className="font-bold">Jami (UZS)</span>
                <span className="font-bold text-green-600">{decision.total_landed_cost_uzs.toLocaleString("uz-UZ")} so'm</span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function fallbackView(response: QueryResponse) {
  if (response.status !== "completed" || response.phases) return null;
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4">Natija</h2>
      <pre className="text-sm text-gray-700 whitespace-pre-wrap">{JSON.stringify(response.result, null, 2)}</pre>
    </div>
  );
}
