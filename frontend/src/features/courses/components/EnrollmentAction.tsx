"use client";

import { ClockIcon, XCircleIcon } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { coursesError } from "../errors";
import { useRequestEnrollment } from "../hooks";
import type { EnrollmentStatus } from "../types";

type EnrollmentActionProps = {
  courseId: number;
  status: EnrollmentStatus | null;
};

/** "Zapisz się" / "Prośba wysłana, czeka na nauczyciela" / "Prośba odrzucona" + "Poproś ponownie". */
export function EnrollmentAction({ courseId, status }: EnrollmentActionProps) {
  const request = useRequestEnrollment(courseId);

  if (status === "accepted") {
    return null;
  }

  return (
    <div className="flex flex-col items-start gap-2 sm:items-end">
      {status === "pending" && (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <ClockIcon aria-hidden="true" className="size-4 shrink-0" />
          Prośba wysłana, czeka na nauczyciela
        </p>
      )}
      {status === "rejected" && (
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <XCircleIcon aria-hidden="true" className="size-4 shrink-0" />
          Prośba odrzucona
        </p>
      )}
      {status !== "pending" && (
        <Button
          variant={status === "rejected" ? "outline" : "default"}
          disabled={request.isPending}
          onClick={() => request.mutate()}
        >
          {request.isPending && <Spinner data-icon="inline-start" />}
          {status === "rejected" ? "Poproś ponownie" : "Zapisz się"}
        </Button>
      )}
      {request.isError && (
        <p role="alert" className="text-sm text-destructive">
          {coursesError(request.error)}
        </p>
      )}
    </div>
  );
}
