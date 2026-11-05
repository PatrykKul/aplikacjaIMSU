import { api } from "@/shared/api/client";

export type Health = {
  status: string;
  database: "ok" | "error";
};

export function getHealth(): Promise<Health> {
  return api.get<Health>("/health");
}
