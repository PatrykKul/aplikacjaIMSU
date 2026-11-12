import { RoleGate } from "@/features/auth/components/RoleGate";
import { SurveyForm } from "@/features/learning-style/components/SurveyForm";

export default function SurveyPage() {
  return (
    <RoleGate roles={["student"]}>
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">
            Ankieta: jak najlepiej się uczysz?
          </h1>
          <p className="text-muted-foreground">
            20 krótkich pytań. Wybierz odpowiedź, która najbardziej do Ciebie
            pasuje; nie ma złych odpowiedzi. Wynik to procenty trzech form:
            wzrokowej, słuchowej i kinestetycznej – lekcje dostaniesz w formie z
            najwyższym procentem. Ankietę wypełnia się raz, potem procenty
            zmieniają wyniki quizów.
          </p>
        </div>
        <SurveyForm />
      </div>
    </RoleGate>
  );
}
