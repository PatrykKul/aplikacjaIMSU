"use client";

import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { teachError } from "../errors";
import { formatDateTime } from "../format";
import { useDecideEnrollment } from "../hooks";
import type { Enrollment } from "../types";

type EnrollmentRequestsProps = {
  courseId: number;
  /** Requests with status `pending`, oldest first. */
  requests: Enrollment[];
};

export function EnrollmentRequests({
  courseId,
  requests,
}: EnrollmentRequestsProps) {
  const decide = useDecideEnrollment(courseId);

  function onDecide(request: Enrollment, accept: boolean) {
    decide.mutate(
      { studentId: request.student.id, accept },
      {
        onSuccess: () =>
          toast.success(
            accept
              ? `Przyjęto na kurs: ${request.student.display_name}.`
              : `Odrzucono prośbę: ${request.student.display_name}. Uczeń może poprosić ponownie.`,
          ),
        onError: (error) => toast.error(teachError(error)),
      },
    );
  }

  if (requests.length === 0) {
    return (
      <p className="text-muted-foreground">
        Nikt nie czeka na decyzję. Nowe prośby uczniów pojawią się tutaj.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Imię</TableHead>
          <TableHead>E-mail</TableHead>
          <TableHead>Prośba z</TableHead>
          <TableHead className="text-right">Decyzja</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {requests.map((request) => {
          const busy =
            decide.isPending &&
            decide.variables?.studentId === request.student.id;
          return (
            <TableRow key={request.student.id}>
              <TableCell className="font-medium">
                {request.student.display_name}
              </TableCell>
              <TableCell>{request.student.email}</TableCell>
              <TableCell>{formatDateTime(request.requested_at)}</TableCell>
              <TableCell>
                <div className="flex justify-end gap-2">
                  <Button
                    size="sm"
                    disabled={busy}
                    aria-label={`Przyjmij: ${request.student.display_name}`}
                    onClick={() => onDecide(request, true)}
                  >
                    Przyjmij
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={busy}
                    aria-label={`Odrzuć: ${request.student.display_name}`}
                    onClick={() => onDecide(request, false)}
                  >
                    Odrzuć
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
