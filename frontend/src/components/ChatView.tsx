"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useChat } from "@/hooks/useChat";
import { AgentTimeline } from "./AgentTimeline";
import { SourcesBadge } from "./SourcesBadge";
import { Message, Language } from "@/lib/types";

const SUGGESTIONS = [
  "Xitoydan nima olib kelsam foydali?",
  "Mini printer import foydalimi?",
  "Lenovo laptop Toshkentga qancha tushadi?",
];

function useLocalStorage<T>(key: string, initial: T): [T, (v: T) => void] {
  const [val, setVal] = useState<T>(() => {
    if (typeof window === "undefined") return initial;
    try {
      const stored = localStorage.getItem(key);
      return stored ? JSON.parse(stored) : initial;
    } catch {
      return initial;
    }
  });
  const set = (v: T) => {
    setVal(v);
    try {
      localStorage.setItem(key, JSON.stringify(v));
    } catch {}
  };
  return [val, set];
}

export function ChatView() {
  const { messages, loading, phases, sendMessage } = useChat();
  const [input, setInput] = useState("");
  const [language, setLanguage] = useLocalStorage<Language>("trade-ai-lang", "uz");
  const [history, setHistory] = useLocalStorage<{ id: string; preview: string; time: string }[]>("trade-ai-history", []);
  const [showHistory, setShowHistory] = useState(false);
  const msgEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, phases]);

  const handleSend = (text: string) => {
    if (!text.trim() || loading) return;
    sendMessage(text.trim(), language);
    setHistory([{ id: Date.now().toString(), preview: text.trim().slice(0, 40), time: new Date().toISOString() }, ...history.filter(h => h.preview !== text.trim().slice(0, 40)).slice(0, 49)]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(input);
    setInput("");
  };

  return (
    <div className="flex h-screen bg-[#212121]">
      {showHistory && (
        <aside className="w-64 bg-[#171717] border-r border-[#2f2f2f] flex flex-col p-3 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-400 font-medium">Chat tarixi</span>
            <button onClick={() => setShowHistory(false)} className="text-gray-500 hover:text-gray-300 text-xs">✕</button>
          </div>
          {history.length === 0 && <p className="text-xs text-gray-600">Hali chatlar yo'q</p>}
          {history.map((h) => (
            <button key={h.id} className="text-left text-xs text-gray-400 hover:text-gray-200 hover:bg-[#2f2f2f] rounded-lg p-2 mb-1 transition-colors">
              {h.preview}
            </button>
          ))}
        </aside>
      )}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between px-4 h-12 border-b border-[#2f2f2f] shrink-0">
          <div className="flex items-center gap-2">
            <button onClick={() => setShowHistory(v => !v)} className="text-gray-400 hover:text-gray-200 p-1">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
            <span className="text-sm font-medium text-gray-200">Trade AI</span>
          </div>
          <div className="flex items-center gap-2">
            <select value={language} onChange={(e) => setLanguage(e.target.value as Language)}
              className="bg-[#2f2f2f] text-gray-300 text-xs rounded-lg px-2 py-1.5 border border-[#3f3f3f] outline-none">
              <option value="uz">O'zbek</option>
              <option value="ru">Русский</option>
              <option value="en">English</option>
            </select>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6">
            <AnimatePresence mode="popLayout">
              {messages.length === 0 && !loading && (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="flex flex-col items-center justify-center min-h-[60vh]">
                  <span className="text-3xl mb-4">🔥</span>
                  <h2 className="text-lg font-medium text-gray-200 mb-1">Import biznes uchun AI</h2>
                  <p className="text-xs text-gray-500 mb-6">Xitoydan O'zbekistonga nima olib kelish foydali</p>
                  <div className="flex flex-col gap-2 w-full max-w-sm">
                    {SUGGESTIONS.map((q) => (
                      <button key={q} onClick={() => handleSend(q)}
                        className="text-xs text-gray-400 bg-[#2f2f2f] hover:bg-[#3f3f3f] rounded-xl px-3 py-2 text-left transition-colors">
                        {q}
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}
              {messages.length > 0 && (
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} />
                  ))}
                  {loading && phases && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-[#2f2f2f]/30 rounded-xl p-3 border border-[#2f2f2f]">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="flex gap-1">
                          {[0, 1, 2].map((i) => (
                            <div key={i} className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"
                              style={{ animationDelay: `${i * 0.16}s`, animationDuration: "1.4s" }} />
                          ))}
                        </div>
                        <span className="text-xs text-gray-500">Agentlar ishlayapti...</span>
                      </div>
                      <AgentTimeline phases={phases} language={language} />
                    </motion.div>
                  )}
                </div>
              )}
              <div ref={msgEndRef} />
            </AnimatePresence>
          </div>
        </main>

        <footer className="border-t border-[#2f2f2f] px-4 py-3 shrink-0">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="flex items-center gap-2 bg-[#2f2f2f] rounded-xl border border-[#3f3f3f] px-3">
              <input ref={inputRef} type="text" value={input} onChange={(e) => setInput(e.target.value)}
                placeholder={language === "uz" ? "Mahsulot nomi..." : language === "ru" ? "Название товара..." : "Product name..."}
                disabled={loading}
                className="flex-1 bg-transparent py-2.5 text-sm text-gray-200 placeholder-gray-600 outline-none" />
              <button type="submit" disabled={loading || !input.trim()}
                className="text-gray-400 hover:text-gray-200 disabled:opacity-30 p-1">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" /></svg>
              </button>
            </div>
          </form>
        </footer>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const [showSources, setShowSources] = useState(false);

  if (message.role === "user") {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-end">
        <div className="max-w-[75%] bg-indigo-600/20 border border-indigo-600/30 rounded-2xl rounded-br-md px-3 py-2">
          <p className="text-sm text-gray-200 whitespace-pre-wrap">{message.content}</p>
        </div>
      </motion.div>
    );
  }

  const answer = message.content;
  const result = message.result;
  const market = result?.market;
  const profit = result?.profit;
  const confidence = result?.confidence;
  const opportunities = result?.opportunities || [];
  const marginPct = profit?.margin_pct ?? 0;
  const overallConf = confidence?.overall ?? 0;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      {answer && (
        <div className="bg-[#2f2f2f]/50 border border-[#2f2f2f] rounded-2xl rounded-bl-md px-3 py-2.5 mb-2">
          <div className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">{answer}</div>
        </div>
      )}

      {profit && (
        <div className="flex items-center gap-3 mb-2 px-1">
          <span className="text-xs text-gray-500">Foyda</span>
          <span className={`text-lg font-bold ${marginPct > 0 ? "text-green-400" : "text-gray-400"}`}>
            {marginPct > 0 ? `+${marginPct}%` : `${marginPct}%`}
          </span>
          {profit.total_landed_usd && <span className="text-xs text-gray-500">Landed: ${profit.total_landed_usd.toFixed(2)}</span>}
        </div>
      )}

      {overallConf > 0 && (
        <div className="flex items-center gap-2 mb-2 px-1">
          <span className="text-xs text-gray-500">Ishonchlilik</span>
          <div className="flex-1 max-w-[120px] h-1 bg-[#3f3f3f] rounded-full overflow-hidden">
            <motion.div className="h-full rounded-full bg-indigo-400" initial={{ width: 0 }}
              animate={{ width: `${overallConf * 100}%` }} transition={{ duration: 0.8 }} />
          </div>
          <span className="text-xs text-gray-400">{Math.round(overallConf * 100)}%</span>
        </div>
      )}

      {market && (
        <>
          <button onClick={() => setShowSources(v => !v)}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors px-1">
            {showSources ? "yashirish" : "manbalar"} {showSources ? "▲" : "▼"}
          </button>
          {showSources && (
            <div className="mt-1">
              <SourcesBadge market={market} opportunities={opportunities} />
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}
