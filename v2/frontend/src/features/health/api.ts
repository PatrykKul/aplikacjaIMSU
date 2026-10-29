import { apiGet } from "@/shared/api/client";

export type Health = {
    status: string;
    database: "ok" | "error";
};

export function getHealth(): Promise<Health> {
    return apiGet<Health>("/health");
}