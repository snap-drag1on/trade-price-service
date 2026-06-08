"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useChat } from "@/hooks/useChat";
import { AgentTimeline } from "./AgentTimeline";
import { OpportunityCard } from "./OpportunityCard";
import { SourcesBadge } from "./SourcesBadge";
import { PhaseData, getPhaseIcon, getPhaseLabel, Language, Message } from "@/lib/types";

export function ChatView() {
  const { messages, loading, phases, sendMessage, reset } = useChat();
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<Language>("uz");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput("");
    await sendMessage(msg, language);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, phases]);

  return (
    <div className="flex flex-col h-screen bg-surface-900">
      <header className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur-xl border-b border-gray-800">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🔥</span>
            <h1 className="text-sm font-semibold text-gray-200">Trade AI</h1>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as Language)}
              className="bg-gray-800 text-gray-300 text-xs rounded-lg px-2 py-1.5 border border-gray-700"
            >
              <option value="uz">O'zbek</option>
              <option value="ru">Русский</option>
              <option value="en">English</option>
            </select>
            {messages.length > 0 && (
              <button
                onClick={reset}
                className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <AnimatePresence mode="popLayout">
            {messages.length === 0 ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center min-h-[60vh]"
              >
                <span className="text-5xl mb-6">🔥</span>
                <h2 className="text-2xl font-bold text-gray-200 mb-3 text-center">
                  Import biznes uchun AI maslahatchi
                </h2>
                <p className="text-sm text-gray-500 text-center max-w-md mb-8">
                  Xitoydan O'zbekistonga nima olib kelish foydali ekanligini toping. 
                  Narxlar, boj, logistika va foydani hisoblaymiz.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-lg">
                  {[
                    "Xitoydan nima olib kelsam foydali?",
                    "Mini printer import foydalimi?",
                    "Lenovo laptop Toshkentga qancha tushadi?",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => { setInput(""); sendMessage(q, language); }}
                      className="text-xs text-gray-400 bg-gray-800/50 border border-gray-700 rounded-xl p-3 hover:border-brand-500/50 hover:text-gray-200 transition-all text-left"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </motion.div>
            ) : (
              <div className="space-y-6">
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
                {loading && phases && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-800/30 border border-gray-800 rounded-2xl p-4"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                          <div
                            key={i}
                            className="w-2 h-2 bg-brand-400 rounded-full animate-pulse-dot"
                            style={{ animationDelay: `${i * 0.16}s` }}
                          />
                        ))}
                      </div>
                      <span className="text-xs text-gray-500">Agentlar ishlamoqda...</span>
                    </div>
                    <AgentTimeline phases={phases} language={language} />
                  </motion.div>
                )}
              </div>
            )}
            <div ref={messagesEndRef} />
          </AnimatePresence>
        </div>
      </main>

      <footer className="sticky bottom-0 bg-surface-900/80 backdrop-blur-xl border-t border-gray-800">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center gap-2 bg-gray-800 rounded-2xl border border-gray-700 focus-within:border-brand-500 transition-colors px-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Mahsulot nomi yoki savolingiz..."
              disabled={loading}
              className="flex-1 bg-transparent py-3 text-sm text-gray-200 placeholder-gray-500 outline-none"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-9 h-9 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
            >
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
          <p className="text-center text-[10px] text-gray-600 mt-1.5">
            Trade AI import bo'yicha yordam beradi. Narxlar taxminiy.
          </p>
        </form>
      </footer>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const [showSources, setShowSources] = useState(false);

  const profitData = message.result?.profit || message.result;
  const marketData = message.result?.market;
  const sources = message.result?.opportunities || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`max-w-[85%] ${isUser ? "" : ""}`}>
        {!isUser && message.phases && (
          <AgentTimeline phases={message.phases} />
        )}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? "bg-brand-600 text-white rounded-br-md"
              : "bg-gray-800/50 border border-gray-800 text-gray-200 rounded-bl-md"
          }`}
        >
          <p className="text-sm whitespace-pre-wrap leading-relaxed">
            {message.content}
          </p>
        </div>

        {!isUser && profitData && (
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
            <OpportunityCard data={profitData} index={0} />
          </div>
        )}

        {!isUser && marketData && (
          <>
            <button
              onClick={() => setShowSources(!showSources)}
              className="mt-2 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              {showSources ? "yashirish" : "manbalarni ko'rsatish"} ▼
            </button>
            {showSources && (
              <SourcesBadge sources={sources} market={marketData} />
            )}
          </>
        )}

        <p className="text-[10px] text-gray-600 mt-1 px-1">
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </motion.div>
  );
}
