export type UserRole = "student" | "teacher" | "admin";

/** Roles of accounts created by registration or by the admin. */
export type ManagedRole = Exclude<UserRole, "admin">;

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
  role: ManagedRole;
};
