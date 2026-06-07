"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import { QueryRequest, QueryResponse } from "@/lib/types";

interface UseQueryState {
  loading: boolean;
  data: QueryResponse | null;
  error: Error | null;
  taskId: string | null;
}

export function useTradeQuery() {
  const [state, setState] = useState<UseQueryState>({
    loading: false,
    data: null,
    error: null,
    taskId: null,
  });

  const createQuery = useCallback(async (request: QueryRequest) => {
    setState({ loading: true, data: null, error: null, taskId: null });

    try {
      const { task_id } = await api.createQuery(request);
      setState((prev) => ({ ...prev, taskId: task_id }));

      const result = await api.pollQuery(task_id);

      setState({
        loading: false,
        data: result,
        error: null,
        taskId: task_id,
      });

      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      setState({
        loading: false,
        data: null,
        error: err,
        taskId: null,
      });
      throw err;
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      loading: false,
      data: null,
      error: null,
      taskId: null,
    });
  }, []);

  return { ...state, createQuery, reset };
}
