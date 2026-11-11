"use client";

import { AlertCircleIcon, CheckIcon, UserPlusIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { classroomsError } from "@/features/classes/errors";
import { useAddStudent, useStudentSearch } from "@/features/classes/hooks";
import { type Classroom, STUDENT_SEARCH_MIN } from "@/features/classes/types";
import { useDebouncedValue } from "@/shared/hooks/use-debounced-value";
import { cn } from "@/shared/lib/utils";
import { Alert, AlertDescription } from "@/shared/ui/alert";
import { Badge } from "@/shared/ui/badge";
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
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";

type AddStudentDialogProps = {
  classroom: Classroom;
  open: boolean;
  onClose: () => void;
};

export function AddStudentDialog({
  classroom,
  open,
  onClose,
}: AddStudentDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          onClose();
        }
      }}
    >
      {/* Mounted only while open, so every opening starts with an empty field */}
      <DialogContent>
        {open && <StudentSearch classroom={classroom} />}
      </DialogContent>
    </Dialog>
  );
}

function StudentSearch({ classroom }: { classroom: Classroom }) {
  const [text, setText] = useState("");
  // The search runs after a short pause in typing, not on every key
  const query = useDebouncedValue(text.trim());
  const search = useStudentSearch(query);
  const addStudent = useAddStudent(classroom.id);
  const memberIds = new Set((classroom.students ?? []).map((s) => s.id));

  let results;
  if (text.trim().length < STUDENT_SEARCH_MIN) {
    results = (
      <p className="text-sm text-muted-foreground">
        Wpisz co najmniej {STUDENT_SEARCH_MIN} znaki adresu e-mail ucznia.
      </p>
    );
  } else if (search.isError) {
    results = (
      <Alert variant="destructive">
        <AlertCircleIcon />
        <AlertDescription>{classroomsError(search.error)}</AlertDescription>
      </Alert>
    );
  } else if (search.data === undefined) {
    results = (
      <div className="flex justify-center py-4">
        <Spinner className="size-5" />
      </div>
    );
  } else if (search.data.length === 0) {
    results = (
      <p className="text-sm text-muted-foreground">
        Nie znaleziono ucznia z takim adresem. Uczeń musi mieć konto w systemie.
      </p>
    );
  } else {
    results = (
      <ul
        role="list"
        className={cn(
          "max-h-72 divide-y overflow-y-auto rounded-xl ring-1 ring-foreground/10 transition-opacity",
          // Results of the previous text while the new ones load
          search.isPlaceholderData && "opacity-60",
        )}
      >
        {search.data.map((student) => {
          const isMember = memberIds.has(student.id);
          const isAdding =
            addStudent.isPending && addStudent.variables === student.id;
          return (
            <li
              key={student.id}
              className="flex items-center gap-3 py-2 pr-2 pl-4"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{student.email}</p>
                <p className="truncate text-sm text-muted-foreground">
                  {student.display_name}
                </p>
              </div>
              {isMember ? (
                <Badge variant="secondary">
                  <CheckIcon data-icon="inline-start" />W klasie
                </Badge>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={isAdding}
                  aria-label={`Dodaj do klasy: ${student.email}`}
                  onClick={() =>
                    addStudent.mutate(student.id, {
                      onSuccess: () =>
                        toast.success(
                          `Dodano do klasy: ${student.display_name}.`,
                        ),
                      onError: (error) => toast.error(classroomsError(error)),
                    })
                  }
                >
                  {isAdding ? (
                    <Spinner data-icon="inline-start" />
                  ) : (
                    <UserPlusIcon data-icon="inline-start" />
                  )}
                  Dodaj
                </Button>
              )}
            </li>
          );
        })}
      </ul>
    );
  }

  return (
    <div className="grid gap-4">
      <DialogHeader>
        <DialogTitle>Dodaj ucznia</DialogTitle>
        <DialogDescription>
          Wyszukaj ucznia po adresie e-mail. Możesz dodać kilku uczniów po
          kolei.
        </DialogDescription>
      </DialogHeader>

      <FormField label="E-mail ucznia">
        {(control) => (
          <Input
            {...control}
            type="search"
            autoComplete="off"
            placeholder="np. jan.kowalski@"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        )}
      </FormField>

      <div aria-live="polite">{results}</div>

      <DialogFooter>
        <DialogClose render={<Button type="button" />}>Gotowe</DialogClose>
      </DialogFooter>
    </div>
  );
}
