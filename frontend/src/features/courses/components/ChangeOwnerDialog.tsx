"use client";

import { useState } from "react";
import { toast } from "sonner";

import { useApprovedTeachers } from "@/features/users/hooks";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Spinner } from "@/shared/ui/spinner";

import { coursesError } from "../errors";
import { useChangeCourseOwner } from "../hooks";
import type { CourseSummary } from "../types";

type ChangeOwnerDialogProps = {
  course: CourseSummary | null;
  onClose: () => void;
};

type Candidate = { id: number; name: string; email: string };

/** Admin: pick an approved teacher, then confirm in an AlertDialog. */
export function ChangeOwnerDialog({ course, onClose }: ChangeOwnerDialogProps) {
  const teachers = useApprovedTeachers(course !== null);
  const change = useChangeCourseOwner();
  const [ownerId, setOwnerId] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  const candidates: Candidate[] = (teachers.data ?? [])
    .filter((teacher) => teacher.id !== course?.owner.id)
    .map((teacher) => ({
      id: teacher.id,
      name: teacher.display_name,
      email: teacher.email,
    }));
  const chosen = candidates.find((c) => String(c.id) === ownerId) ?? null;

  function close() {
    setOwnerId(null);
    setConfirming(false);
    onClose();
  }

  function submit() {
    if (!course || !chosen) {
      return;
    }
    change.mutate(
      { courseId: course.id, ownerId: chosen.id },
      {
        onSuccess: (updated) => {
          toast.success(
            `Kurs „${updated.title}” ma nowego autora: ${updated.owner.display_name}.`,
          );
          close();
        },
        onError: (error) => {
          toast.error(coursesError(error));
          setConfirming(false);
        },
      },
    );
  }

  return (
    <>
      <Dialog
        open={course !== null && !confirming}
        onOpenChange={(open) => {
          if (!open) {
            close();
          }
        }}
      >
        <DialogContent>
          {course && (
            <div className="grid gap-4">
              <DialogHeader>
                <DialogTitle>Zmień właściciela kursu</DialogTitle>
                <DialogDescription>
                  „{course.title}” – obecny autor: {course.owner.display_name}.
                  Zapisy uczniów, wyniki i statystyki zostają bez zmian.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-2">
                <Label htmlFor="new-owner">Nowy autor</Label>
                {teachers.isPending ? (
                  <Spinner className="size-5" />
                ) : candidates.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Nie ma innego zatwierdzonego nauczyciela.
                  </p>
                ) : (
                  <Select
                    value={ownerId}
                    onValueChange={(value) => setOwnerId(value)}
                    items={candidates.map((c) => ({
                      value: String(c.id),
                      label: `${c.name} (${c.email})`,
                    }))}
                  >
                    <SelectTrigger id="new-owner" className="w-full">
                      <SelectValue placeholder="Wybierz nauczyciela" />
                    </SelectTrigger>
                    <SelectContent>
                      {candidates.map((c) => (
                        <SelectItem key={c.id} value={String(c.id)}>
                          {c.name} ({c.email})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
              <DialogFooter>
                <DialogClose
                  render={<Button type="button" variant="outline" />}
                >
                  Anuluj
                </DialogClose>
                <Button
                  type="button"
                  disabled={!chosen}
                  onClick={() => setConfirming(true)}
                >
                  Dalej
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={course !== null && confirming}
        onOpenChange={(open) => {
          if (!open) {
            setConfirming(false);
          }
        }}
      >
        <AlertDialogContent>
          {course && chosen && (
            <>
              <AlertDialogHeader>
                <AlertDialogTitle>Przekazać kurs?</AlertDialogTitle>
                <AlertDialogDescription>
                  Kurs „{course.title}” przejdzie od {course.owner.display_name}{" "}
                  do {chosen.name}. Nowy autor zobaczy go w swoim panelu i
                  będzie mógł go edytować; poprzedni straci do niego dostęp.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Wróć</AlertDialogCancel>
                <AlertDialogAction disabled={change.isPending} onClick={submit}>
                  {change.isPending && <Spinner data-icon="inline-start" />}
                  Zmień właściciela
                </AlertDialogAction>
              </AlertDialogFooter>
            </>
          )}
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
