"use client";

import { useState } from "react";
import { useTradeQuery } from "@/hooks/useQuery";

export function QueryForm() {
  const [product, setProduct] = useState("");
  const [language, setLanguage] = useState<"uz" | "ru" | "en">("uz");
  const { createQuery, loading, data, error } = useTradeQuery();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product.trim()) return;

    await createQuery({
      product: product.trim(),
      language,
      destination: "UZ",
      use_cache: true,
    });
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Mahsulot nomi... (misol: Dell XPS laptop)"
            value={product}
            onChange={(e) => setProduct(e.target.value)}
            disabled={loading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={loading || !product.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {loading ? "Qidirilmoqda..." : "Qidirish"}
          </button>
        </div>

        <div className="flex gap-4">
          {[
            { value: "uz", label: "O'zbek" },
            { value: "ru", label: "Русский" },
            { value: "en", label: "English" },
          ].map((lang) => (
            <label key={lang.value} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="language"
                value={lang.value}
                checked={language === lang.value}
                onChange={(e) => setLanguage(e.target.value as any)}
                disabled={loading}
                className="w-4 h-4 text-blue-600"
              />
              <span className="text-sm text-gray-700">{lang.label}</span>
            </label>
          ))}
        </div>
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error.message}</p>
        </div>
      )}
    </div>
  );
}
