"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";

import { ApiError } from "./client";

function shouldRetry(failureCount: number, error: Error): boolean {
  // Client errors (4xx) will not fix themselves, so don't retry them
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            refetchOnWindowFocus: false,
            retry: shouldRetry,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
