const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export class ApiError extends Error {
    readonly status: number;
    readonly code?: string;

    constructor(status: number, code?: string) {
        super(code ?? `HTTP ${status}`);
        this.status = status;
        this.code = code;
    }
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${API_URL}${path}`, {
        ...init,
        headers: { Accept: "application/json", ...init?.headers },
    });
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new ApiError(response.status, body?.code);
    }
    return (await response.json()) as T;
}