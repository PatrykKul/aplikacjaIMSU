import type { ApprovalStatus, User, UserRole } from "./types";

export const roleLabels: Record<UserRole, string> = {
  student: "Uczeń",
  teacher: "Nauczyciel",
  admin: "Administrator",
};

export const approvalLabels: Record<ApprovalStatus, string> = {
  approved: "Zatwierdzone",
  pending: "Czeka na zatwierdzenie",
  rejected: "Odrzucone",
};

export const PENDING_PATH = "/pending";

/** A teacher account the admin has not approved (yet or at all). */
export function isUnapprovedTeacher(user: User): boolean {
  return user.role === "teacher" && user.approval_status !== "approved";
}

/** Where a signed-in user starts: the dashboard, or the waiting screen. */
export function homePath(user: User): string {
  return isUnapprovedTeacher(user) ? PENDING_PATH : "/dashboard";
}
