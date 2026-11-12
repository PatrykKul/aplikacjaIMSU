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
  approvedTeachers: () =>
    api.get<User[]>("/users?role=teacher&approval=approved"),
  create: (data: UserCreateInput) => api.post<User>("/users", data),
  update: (id: number, data: UserUpdateInput) =>
    api.patch<User>(`/users/${id}`, data),
  approve: (id: number) => api.post<User>(`/users/${id}/approve`),
  reject: (id: number) => api.post<User>(`/users/${id}/reject`),
};
