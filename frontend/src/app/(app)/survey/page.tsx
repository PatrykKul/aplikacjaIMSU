import { RoleGate } from "@/features/auth/components/RoleGate";
import { SurveyForm } from "@/features/learning-style/components/SurveyForm";

export default function SurveyPage() {
  return (
    <RoleGate roles={["student"]}>
      <div className="mx-auto max-w-2xl space-y-6">
        <SurveyForm />
      </div>
    </RoleGate>
  );
}
