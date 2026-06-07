import axios from "axios";
import { QueryRequest, QueryResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8003/api/v1";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  async createQuery(req: QueryRequest): Promise<{ task_id: string }> {
    const response = await client.post("/query", req);
    return response.data;
  },

  async getQueryStatus(taskId: string): Promise<QueryResponse> {
    const response = await client.get(`/query/${taskId}`);
    return response.data;
  },

  async pollQuery(taskId: string, maxAttempts = 60, interval = 5000): Promise<QueryResponse> {
    for (let i = 0; i < maxAttempts; i++) {
      const result = await this.getQueryStatus(taskId);
      if (result.status === "completed" || result.status === "error") {
        return result;
      }
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
    throw new Error("Query timeout");
  },

  async checkPrice(product: string, price: number, origin: string) {
    const response = await client.post("/price-check", {
      product_query: product,
      origin,
      destination: "UZ",
      price_original: price,
      currency: "USD",
      transport_mode: "rail",
    });
    return response.data;
  },

  async health() {
    const response = await client.get("/health");
    return response.data;
  },
};
