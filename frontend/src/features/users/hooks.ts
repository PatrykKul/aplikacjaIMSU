import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { ManagedRole, User } from "@/features/auth/types";

import { type UserUpdateInput, usersApi } from "./api";

export const usersKey = (role: ManagedRole) => ["users", role] as const;

export function useUsers(role: ManagedRole) {
  return useQuery({
    queryKey: usersKey(role),
    queryFn: () => usersApi.list(role),
  });
}

function useRefreshUsers() {
  const queryClient = useQueryClient();
  // The list is sorted by e-mail on the server, so refetch instead of patching the cache
  return (user: User) =>
    queryClient.invalidateQueries({ queryKey: ["users", user.role] });
}

export function useCreateUser() {
  const refresh = useRefreshUsers();
  return useMutation({ mutationFn: usersApi.create, onSuccess: refresh });
}

export function useUpdateUser() {
  const refresh = useRefreshUsers();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UserUpdateInput }) =>
      usersApi.update(id, data),
    onSuccess: refresh,
  });
}

/** Admin's decision on a teacher account: `approve` or `reject`. */
export function useDecideApproval() {
  const refresh = useRefreshUsers();
  return useMutation({
    mutationFn: ({ id, approve }: { id: number; approve: boolean }) =>
      approve ? usersApi.approve(id) : usersApi.reject(id),
    onSuccess: refresh,
  });
}
