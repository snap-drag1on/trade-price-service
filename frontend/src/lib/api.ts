import axios from "axios";
import { QueryRequest, QueryResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://trade-price-service.onrender.com/api/v1";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  async createQuery(req: QueryRequest): Promise<{ task_id: string }> {
    const { data } = await client.post("/query", req);
    return data;
  },

  async getQueryStatus(taskId: string): Promise<QueryResponse> {
    const { data } = await client.get(`/query/${taskId}`);
    return data;
  },

  async pollQuery(
    taskId: string,
    onProgress?: (phases: Record<string, any>) => void,
    maxAttempts = 90,
    interval = 2000,
  ): Promise<QueryResponse> {
    for (let i = 0; i < maxAttempts; i++) {
      const result = await this.getQueryStatus(taskId);
      if (result.phases && onProgress) {
        onProgress(result.phases);
      }
      if (result.status === "completed" || result.status === "error") {
        return result;
      }
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
    throw new Error("Query timeout after " + (maxAttempts * interval / 1000) + "s");
  },

  async checkPrice(product: string, price: number, origin: string) {
    const { data } = await client.post("/price-check", {
      product_query: product,
      origin,
      destination: "UZ",
      price_original: price,
      currency: "USD",
      transport_mode: "rail",
    });
    return data;
  },

  async health() {
    const { data } = await client.get("/health");
    return data;
  },
};
