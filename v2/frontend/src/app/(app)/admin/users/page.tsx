import { RoleGate } from "@/features/auth/components/RoleGate";
import { UsersTable } from "@/features/users/components/UsersTable";

export default function AdminUsersPage() {
  return (
    <RoleGate roles={["admin"]}>
      <UsersTable />
    </RoleGate>
  );
}
