import { RoleGate } from "@/features/auth/components/RoleGate";
import { SurveyResult } from "@/features/learning-style/components/SurveyResult";

export default function SurveyResultPage() {
  return (
    <RoleGate roles={["student"]}>
      <div className="mx-auto max-w-2xl">
        <SurveyResult />
      </div>
    </RoleGate>
  );
}
