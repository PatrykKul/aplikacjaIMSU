import { RoleGate } from "@/features/auth/components/RoleGate";
import { UsersPage } from "@/features/users/components/UsersPage";

export default function AdminUsersPage() {
  return (
    <RoleGate roles={["admin"]}>
      <UsersPage />
    </RoleGate>
  );
}
