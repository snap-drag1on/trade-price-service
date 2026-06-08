"use client";

import { useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { Message, QueryRequest, PhaseData, QueryResponse } from "@/lib/types";

interface UseChatState {
  messages: Message[];
  loading: boolean;
  taskId: string | null;
  phases: Record<string, PhaseData> | null;
  error: string | null;
}

export function useChat() {
  const [state, setState] = useState<UseChatState>({
    messages: [],
    loading: false,
    taskId: null,
    phases: null,
    error: null,
  });

  const taskIdRef = useRef<string | null>(null);

  const updatePhase = useCallback((phases: Record<string, PhaseData>) => {
    setState((prev) => ({ ...prev, phases }));
  }, []);

  const sendMessage = useCallback(async (product: string, language: "uz" | "ru" | "en" = "uz") => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: product,
      timestamp: new Date(),
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMsg],
      loading: true,
      error: null,
      phases: null,
    }));

    try {
      const { task_id } = await api.createQuery({
        product,
        language,
        destination: "UZ",
        use_cache: false,
      });
      taskIdRef.current = task_id;
      setState((prev) => ({ ...prev, taskId: task_id }));

      const result = await api.pollQuery(task_id, updatePhase);

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: result.result?.answer || extractAnswer(result),
        phases: result.phases || undefined,
        result: result.result,
        timestamp: new Date(),
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMsg],
        loading: false,
        phases: result.phases || null,
        taskId: task_id,
      }));

      return result;
    } catch (err) {
      let errorMsg = "Xatolik yuz berdi";
      if (err instanceof Error) {
        if (err.message.includes("404")) errorMsg = "Serverda xatolik, qaytadan urinib ko'ring";
        else errorMsg = err.message;
      }
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `❌ Xatolik: ${errorMsg}`,
        timestamp: new Date(),
      };
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMsg],
        loading: false,
        error: errorMsg,
      }));
      throw err;
    }
  }, [updatePhase]);

  const reset = useCallback(() => {
    taskIdRef.current = null;
    setState({
      messages: [],
      loading: false,
      taskId: null,
      phases: null,
      error: null,
    });
  }, []);

  return { ...state, sendMessage, reset };
}

function extractAnswer(result: QueryResponse): string {
  if (!result.result) return "Natija topilmadi.";
  if (typeof result.result === "string") return result.result;
  if (result.result.answer) return result.result.answer;
  const answer = result.result.decision?.answer || result.result.answer;
  if (answer) return answer;
  try {
    return JSON.stringify(result.result, null, 2);
  } catch {
    return "Natija topildi.";
  }
}
