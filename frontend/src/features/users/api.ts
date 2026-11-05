import type { User, UserRole } from "@/features/auth/types";
import { api } from "@/shared/api/client";

export type UserUpdateInput = {
  role?: UserRole;
  is_active?: boolean;
};

export const usersApi = {
  list: () => api.get<User[]>("/users"),
  update: (id: number, data: UserUpdateInput) =>
    api.patch<User>(`/users/${id}`, data),
};
