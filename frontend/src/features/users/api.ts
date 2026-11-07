import type { ManagedRole, User } from "@/features/auth/types";
import { api } from "@/shared/api/client";

export type UserCreateInput = {
  email: string;
  password: string;
  display_name: string;
  role: ManagedRole;
};

export type UserUpdateInput = {
  display_name?: string;
  email?: string;
  password?: string;
  is_active?: boolean;
};

export const usersApi = {
  list: (role: ManagedRole) => api.get<User[]>(`/users?role=${role}`),
  create: (data: UserCreateInput) => api.post<User>("/users", data),
  update: (id: number, data: UserUpdateInput) =>
    api.patch<User>(`/users/${id}`, data),
};
