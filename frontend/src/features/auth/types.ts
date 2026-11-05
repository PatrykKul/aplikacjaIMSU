export type UserRole = "student" | "teacher" | "admin";

export type User = {
  id: number;
  email: string;
  display_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type RegisterInput = LoginInput & {
  display_name: string;
  role: Exclude<UserRole, "admin">;
};
