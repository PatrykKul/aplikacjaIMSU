import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/shared/api/client";

import { authApi } from "./api";
import type { User } from "./types";

export const currentUserKey = ["auth", "me"] as const;

async function fetchCurrentUser(): Promise<User | null> {
  try {
    return await authApi.me();
  } catch (error) {
    // 401 is not an error here - it means "nobody is logged in"
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export function useCurrentUser() {
  return useQuery({ queryKey: currentUserKey, queryFn: fetchCurrentUser });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (user) => queryClient.setQueryData(currentUserKey, user),
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (user) => queryClient.setQueryData(currentUserKey, user),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      // Drop all cached data of the previous user, then mark "logged out"
      queryClient.clear();
      queryClient.setQueryData(currentUserKey, null);
    },
  });
}
