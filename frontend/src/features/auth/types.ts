export type UserRole = "student" | "teacher" | "admin";

/** Roles of accounts created by registration or by the admin. */
export type ManagedRole = Exclude<UserRole, "admin">;

/** A teacher who registered waits for the admin; everyone else is `approved`. */
export type ApprovalStatus = "approved" | "pending" | "rejected";

export type User = {
  id: number;
  email: string;
  display_name: string;
  role: UserRole;
  is_active: boolean;
  approval_status: ApprovalStatus;
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
