import { RoleGate } from "@/features/auth/components/RoleGate";
import { ProgressPage } from "@/features/progress/components/ProgressPage";

export default function MyProgressPage() {
  return (
    <RoleGate roles={["student"]}>
      <ProgressPage />
    </RoleGate>
  );
}
