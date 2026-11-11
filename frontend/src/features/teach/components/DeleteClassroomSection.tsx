"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { classroomsError } from "@/features/classes/errors";
import { useDeleteClassroom } from "@/features/classes/hooks";
import type { Classroom } from "@/features/classes/types";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/shared/ui/alert-dialog";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

export function DeleteClassroomSection({
  classroom,
}: {
  classroom: Classroom;
}) {
  const router = useRouter();
  const deleteClassroom = useDeleteClassroom(classroom.id);

  return (
    <section
      aria-labelledby="classroom-delete"
      className="space-y-3 border-t pt-6"
    >
      <h2 id="classroom-delete" className="text-xl font-semibold">
        Usuwanie klasy
      </h2>
      <p className="max-w-[65ch] text-muted-foreground">
        Uczniowie stracą dostęp do prywatnych kursów tej klasy. Kursy i konta
        uczniów zostaną.
      </p>
      <AlertDialog>
        <AlertDialogTrigger render={<Button variant="destructive" />}>
          Usuń klasę
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Usunąć klasę?</AlertDialogTitle>
            <AlertDialogDescription>
              Klasa „{classroom.name}” zostanie usunięta. Uczniowie stracą
              dostęp do prywatnych kursów tej klasy. Kursy i konta uczniów
              zostaną.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={deleteClassroom.isPending}
              onClick={() =>
                deleteClassroom.mutate(undefined, {
                  onSuccess: () => {
                    toast.success(`Usunięto klasę: ${classroom.name}.`);
                    router.replace("/teach/classes");
                  },
                  onError: (error) => toast.error(classroomsError(error)),
                })
              }
            >
              {deleteClassroom.isPending && (
                <Spinner data-icon="inline-start" />
              )}
              Usuń klasę
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
