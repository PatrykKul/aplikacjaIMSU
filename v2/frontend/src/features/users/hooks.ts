import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { User } from "@/features/auth/types";

import { type UserUpdateInput, usersApi } from "./api";

export const usersKey = ["users"] as const;

export function useUsers() {
  return useQuery({ queryKey: usersKey, queryFn: usersApi.list });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UserUpdateInput }) =>
      usersApi.update(id, data),
    onSuccess: (updated) =>
      queryClient.setQueryData<User[]>(usersKey, (users) =>
        users?.map((user) => (user.id === updated.id ? updated : user)),
      ),
  });
}
