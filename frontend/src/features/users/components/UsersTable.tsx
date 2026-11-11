"use client";

import { CloudOffIcon, PlusIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import type { ManagedRole, User } from "@/features/auth/types";
import { errorMessage } from "@/shared/api/error-messages";
import { PageMessage } from "@/shared/layout/page-states";
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
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { useUpdateUser, useUsers } from "../hooks";
import { type FormTarget, UserFormDialog } from "./UserFormDialog";

const texts: Record<ManagedRole, { add: string; empty: string }> = {
  teacher: {
    add: "Dodaj nauczyciela",
    empty: "Nie ma jeszcze nauczycieli.",
  },
  student: { add: "Dodaj ucznia", empty: "Nie ma jeszcze uczniów." },
};

const dateFormat = new Intl.DateTimeFormat("pl-PL", { dateStyle: "medium" });

function StatusBadge({ isActive }: { isActive: boolean }) {
  return (
    <Badge variant={isActive ? "secondary" : "destructive"}>
      {isActive ? "Aktywny" : "Zablokowany"}
    </Badge>
  );
}

export function UsersTable({ role }: { role: ManagedRole }) {
  const { data: users, isPending, isError, refetch } = useUsers(role);
  const updateUser = useUpdateUser();
  const [formTarget, setFormTarget] = useState<FormTarget | null>(null);
  const [blockTarget, setBlockTarget] = useState<User | null>(null);

  if (isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (isError) {
    return (
      <PageMessage
        icon={CloudOffIcon}
        title="Nie udało się wczytać użytkowników"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  function toggleActive(user: User) {
    updateUser.mutate(
      { id: user.id, data: { is_active: !user.is_active } },
      {
        onSuccess: (updated) => {
          toast.success(
            updated.is_active
              ? `Odblokowano konto: ${updated.display_name}.`
              : `Zablokowano konto: ${updated.display_name}.`,
          );
          setBlockTarget(null);
        },
        onError: (error) => toast.error(errorMessage(error)),
      },
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Liczba kont: {users.length}
        </p>
        <Button onClick={() => setFormTarget({ role })}>
          <PlusIcon data-icon="inline-start" />
          {texts[role].add}
        </Button>
      </div>

      {users.length === 0 ? (
        <p className="py-12 text-center text-muted-foreground">
          {texts[role].empty}
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Imię</TableHead>
              <TableHead>E-mail</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Założone</TableHead>
              <TableHead className="text-right">Akcje</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">
                  {user.display_name}
                </TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <StatusBadge isActive={user.is_active} />
                </TableCell>
                <TableCell>
                  {dateFormat.format(new Date(user.created_at))}
                </TableCell>
                <TableCell>
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setFormTarget({ role, user })}
                      aria-label={`Edytuj: ${user.display_name}`}
                    >
                      Edytuj
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setBlockTarget(user)}
                    >
                      {user.is_active ? "Zablokuj" : "Odblokuj"}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <UserFormDialog
        // New key = fresh form with the values of the chosen account
        key={formTarget ? (formTarget.user?.id ?? "new") : "closed"}
        target={formTarget}
        onClose={() => setFormTarget(null)}
      />

      <AlertDialog
        open={blockTarget !== null}
        onOpenChange={(open) => {
          if (!open) {
            setBlockTarget(null);
          }
        }}
      >
        <AlertDialogContent>
          {blockTarget && (
            <>
              <AlertDialogHeader>
                <AlertDialogTitle>
                  {blockTarget.is_active
                    ? "Zablokować konto?"
                    : "Odblokować konto?"}
                </AlertDialogTitle>
                <AlertDialogDescription>
                  {blockTarget.is_active
                    ? `${blockTarget.display_name} od razu straci dostęp do systemu.`
                    : `${blockTarget.display_name} znów będzie mieć dostęp do systemu.`}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Anuluj</AlertDialogCancel>
                <AlertDialogAction
                  variant={blockTarget.is_active ? "destructive" : "default"}
                  disabled={updateUser.isPending}
                  onClick={() => toggleActive(blockTarget)}
                >
                  {updateUser.isPending && <Spinner data-icon="inline-start" />}
                  {blockTarget.is_active ? "Zablokuj" : "Odblokuj"}
                </AlertDialogAction>
              </AlertDialogFooter>
            </>
          )}
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
