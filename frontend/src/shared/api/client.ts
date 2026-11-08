const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const TIMEOUT_MS = 10_000;

export type FieldError = { field: string; type: string };

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: FieldError[];

  constructor(status: number, code: string, fields: FieldError[] = []) {
    super(code);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      credentials: "include",
      signal: AbortSignal.timeout(TIMEOUT_MS),
      headers: {
        Accept: "application/json",
        ...(body !== undefined && { "Content-Type": "application/json" }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    // Server unreachable or request timed out
    throw new ApiError(0, "NETWORK_ERROR");
  }

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      data?.code ?? "UNKNOWN_ERROR",
      data?.fields ?? [],
    );
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  delete: <T = void>(path: string) => request<T>("DELETE", path),
};

/** Absolute address of an API path, e.g. an uploaded file in <img src>. */
export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

/**
 * Sends a file as multipart/form-data in the field `file`. Uses XMLHttpRequest
 * because fetch cannot report upload progress; no timeout (large videos).
 * `onProgress` gets the sent part of the file, from 0 to 1.
 */
export function uploadFile<T>(
  path: string,
  file: File,
  onProgress?: (fraction: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}${path}`);
    xhr.withCredentials = true;
    xhr.responseType = "json";
    xhr.setRequestHeader("Accept", "application/json");
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress?.(event.loaded / event.total);
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.response as T);
        return;
      }
      const data = xhr.response;
      reject(
        new ApiError(
          xhr.status,
          data?.code ?? "UNKNOWN_ERROR",
          data?.fields ?? [],
        ),
      );
    };
    xhr.onerror = () => reject(new ApiError(0, "NETWORK_ERROR"));

    const body = new FormData();
    body.append("file", file);
    xhr.send(body);
  });
}
