import { api } from "@/shared/api/client";

import type { LoginInput, RegisterInput, User } from "./types";

export const authApi = {
  me: () => api.get<User>("/auth/me"),
  login: (data: LoginInput) => api.post<User>("/auth/login", data),
  register: (data: RegisterInput) => api.post<User>("/auth/register", data),
  logout: () => api.post<void>("/auth/logout"),
};
