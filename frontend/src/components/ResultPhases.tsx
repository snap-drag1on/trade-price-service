"use client";

import { QueryResponse } from "@/lib/types";

interface ResultPhasesProps {
  response: QueryResponse;
}

export function ResultPhases({ response }: ResultPhasesProps) {
  if (!response.phases) return null;

  const { discovery, analyst, decision } = response.phases;

  return (
    <div className="space-y-6 mt-8 w-full max-w-3xl mx-auto">
      {discovery && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-blue-900 mb-4">
            1. Narxlar ({discovery.total_sources} manbadan)
          </h2>
          <div className="space-y-3">
            {discovery.sources.map((source, idx) => (
              <div key={idx} className="bg-white p-4 rounded border border-blue-100 flex justify-between items-start">
                <div>
                  <p className="font-semibold">{source.source.toUpperCase()}</p>
                  <p className="text-gray-600 text-sm">{source.product_name}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Ishonchlilik: {(source.confidence * 100).toFixed(0)}%
                  </p>
                  <a
                    href={source.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 text-xs hover:underline"
                  >
                    Manba
                  </a>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-green-600">
                    ${source.price.toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500">{source.currency}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 bg-white p-4 rounded border-l-4 border-blue-500">
            <p className="text-gray-700">
              <strong>O'rtacha:</strong>{" "}
              <span className="text-xl font-bold text-blue-600">
                ${discovery.average_price_usd.toFixed(2)}
              </span>
            </p>
          </div>
        </div>
      )}

      {analyst && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-orange-900 mb-4">
            2. Import Tahlili
          </h2>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-white p-4 rounded border border-orange-100">
              <p className="text-gray-600 text-xs">HS Kod</p>
              <p className="text-xl font-bold">{analyst.hs_code}</p>
              <p className="text-xs text-gray-500">{analyst.hs_description}</p>
            </div>
            <div className="bg-white p-4 rounded border border-orange-100">
              <p className="text-gray-600 text-xs">Boj</p>
              <p className="text-xl font-bold text-orange-600">{analyst.duty_rate}%</p>
            </div>
            <div className="bg-white p-4 rounded border border-orange-100">
              <p className="text-gray-600 text-xs">QQS (VAT)</p>
              <p className="text-xl font-bold text-orange-600">{analyst.vat_rate}%</p>
            </div>
            <div className="bg-white p-4 rounded border border-orange-100">
              <p className="text-gray-600 text-xs">Yuk narxi</p>
              <p className="text-xl font-bold">${analyst.freight.cost_usd}</p>
              <p className="text-xs text-gray-500">{analyst.freight.days} kun</p>
            </div>
          </div>
          {analyst.certifications.length > 0 && (
            <div className="bg-white p-4 rounded border border-orange-100">
              <p className="font-semibold mb-2 text-sm">Sertifikatlar</p>
              <ul className="space-y-1 text-sm">
                {analyst.certifications.map((cert, idx) => (
                  <li key={idx} className="text-gray-700">
                    {cert.type}: ${cert.cost_usd} ({cert.duration_days} kun)
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {decision && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-green-900 mb-4">
            3. Yakuniy Hisob
          </h2>
          <div className="bg-white p-6 rounded border-2 border-green-200 mb-4 space-y-3">
            {[
              { label: "Mahsulot", value: decision.breakdown.product, color: "" },
              { label: "Boj", value: decision.breakdown.duty, color: "text-orange-600" },
              { label: "QQS", value: decision.breakdown.vat, color: "text-orange-600" },
              { label: "Yuk", value: decision.breakdown.freight, color: "text-orange-600" },
            ].map((item) => (
              <div key={item.label} className="flex justify-between text-lg">
                <span>{item.label}</span>
                <span className={`font-semibold ${item.color}`}>
                  ${(item.value || 0).toFixed(2)}
                </span>
              </div>
            ))}
            <div className="border-t-2 pt-3 flex justify-between text-xl">
              <span className="font-bold">Jami (USD)</span>
              <span className="font-bold text-green-600 text-2xl">
                ${decision.total_landed_cost_usd.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between text-lg">
              <span className="font-bold">Jami (UZS)</span>
              <span className="font-bold text-green-600">
                {decision.total_landed_cost_uzs.toLocaleString("uz-UZ")} so'm
              </span>
            </div>
          </div>
          {decision.recommendations.length > 0 && (
            <div className="bg-green-100 border-l-4 border-green-600 p-4 rounded">
              <p className="font-bold text-green-900 mb-2">Tavsiya:</p>
              {decision.recommendations.map((rec, idx) => (
                <div key={idx} className="mb-2">
                  <p className="text-green-900">
                    <strong>{rec.source.toUpperCase()}</strong> — {rec.reason}
                  </p>
                  <p className="text-sm text-green-700">
                    Jami: ${(rec.total_with_import || 0).toFixed(2)}
                  </p>
                </div>
              ))}
              {decision.summary && (
                <p className="text-green-900 mt-3 font-semibold">{decision.summary}</p>
              )}
            </div>
          )}
        </div>
      )}

      {response.status === "completed" && !response.phases && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Natija</h2>
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(response.result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
