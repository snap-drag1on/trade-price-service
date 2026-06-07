"use client";

import { useState } from "react";
import { QueryForm } from "@/components/QueryForm";
import { ResultPhases } from "@/components/ResultPhases";
import { useTradeQuery } from "@/hooks/useQuery";

export default function Home() {
  const { loading, data, error } = useTradeQuery();

  return (
    <main className="container mx-auto px-4 py-8">
      <header className="text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Trade Price Service
        </h1>
        <p className="text-lg text-gray-600">
          Import qilmoqchi bo&apos;lgan mahsulotingiz narxini hisoblang
        </p>
      </header>

      <QueryForm />

      {loading && !data && (
        <div className="mt-8 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-600">
            Agentlar tahlil qilmoqda (bu 1-2 daqiqa olishi mumkin)...
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Router, Discovery, Trade Analyst, Decision
          </p>
        </div>
      )}

      {error && (
        <div className="mt-8 max-w-2xl mx-auto p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 font-medium">Xatolik:</p>
          <p className="text-red-600 text-sm mt-1">{error.message}</p>
        </div>
      )}

      {data && data.status === "completed" && <ResultPhases response={data} />}
    </main>
  );
}
