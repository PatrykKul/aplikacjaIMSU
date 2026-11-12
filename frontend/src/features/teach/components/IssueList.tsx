import { AREA_LABELS, groupIssues, issueText } from "../readiness";
import type { IssueArea, ReadinessIssue } from "../types";

type IssueListProps = {
  issues: ReadinessIssue[];
  /** Turns the area names into buttons that open the matching tab. */
  onShowArea?: (area: IssueArea) => void;
};

/** Missing parts of a lesson (R11), grouped by the editor tab they belong to. */
export function IssueList({ issues, onShowArea }: IssueListProps) {
  return (
    <ul role="list" className="space-y-3">
      {groupIssues(issues).map(({ area, issues: inArea }) => (
        <li key={area} className="space-y-1">
          {onShowArea ? (
            <button
              type="button"
              onClick={() => onShowArea(area)}
              className="rounded-sm font-medium underline underline-offset-4 outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              {AREA_LABELS[area]}
            </button>
          ) : (
            <p className="font-medium">{AREA_LABELS[area]}</p>
          )}
          <ul role="list" className="list-disc space-y-0.5 pl-5">
            {inArea.map((issue) => (
              <li key={`${issue.code}-${issue.area}`}>{issueText(issue)}</li>
            ))}
          </ul>
        </li>
      ))}
    </ul>
  );
}
