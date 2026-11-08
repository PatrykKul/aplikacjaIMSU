import { RoleGate } from "@/features/auth/components/RoleGate";
import { LearningStylePanel } from "@/features/learning-style/components/LearningStylePanel";

export default function ProfilePage() {
  return (
    <RoleGate roles={["student"]}>
      <div className="mx-auto max-w-2xl">
        <LearningStylePanel />
      </div>
    </RoleGate>
  );
}
