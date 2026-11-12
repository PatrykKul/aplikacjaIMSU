import { AlertCircleIcon } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";

import { errorIssues, teachError } from "../errors";
import { IssueList } from "./IssueList";

/** Error of a save; 409 PUBLISHED_LESSON_INCOMPLETE also lists what would be missing. */
export function SaveErrorAlert({ error }: { error: unknown }) {
  const issues = errorIssues(error);
  return (
    <Alert variant="destructive">
      <AlertCircleIcon />
      <AlertTitle>Nie zapisano zmian</AlertTitle>
      <AlertDescription className="space-y-3">
        <p>{teachError(error)}</p>
        {issues.length > 0 && <IssueList issues={issues} />}
      </AlertDescription>
    </Alert>
  );
}
