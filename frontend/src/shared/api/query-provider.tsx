"use client";

import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { type ReactNode, useState } from "react";

import { ApiError } from "./client";

function shouldRetry(failureCount: number, error: Error): boolean {
  // Client errors (4xx) will not fix themselves, so don't retry them
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

// A teacher rejected by the admin during the session: reload the account,
// so the guards send them to the approval screen
function createClient(): QueryClient {
  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({ onError: (error) => onApiError(error) }),
    mutationCache: new MutationCache({ onError: (error) => onApiError(error) }),
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        refetchOnWindowFocus: false,
        retry: shouldRetry,
      },
    },
  });
  function onApiError(error: Error) {
    if (error instanceof ApiError && error.code === "TEACHER_NOT_APPROVED") {
      void client.invalidateQueries({ queryKey: ["auth", "me"] });
    }
  }
  return client;
}

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createClient);

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
