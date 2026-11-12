"use client";

import { CloudOffIcon, PlusIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { approvalLabels } from "@/features/auth/roles";
import type { ManagedRole, User } from "@/features/auth/types";
import { errorMessage } from "@/shared/api/error-messages";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
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
import { Spinner } from "@/shared/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { useDecideApproval, useUpdateUser, useUsers } from "../hooks";
import { type FormTarget, UserFormDialog } from "./UserFormDialog";

const texts: Record<ManagedRole, { add: string; empty: string }> = {
  teacher: {
    add: "Dodaj nauczyciela",
    empty: "Nie ma jeszcze nauczycieli.",
  },
  student: { add: "Dodaj ucznia", empty: "Nie ma jeszcze uczniów." },
};

const dateFormat = new Intl.DateTimeFormat("pl-PL", { dateStyle: "medium" });

type Filter = "all" | "pending";

// States as plain text: the words carry the meaning, not a coloured badge
function StatusText({ isActive }: { isActive: boolean }) {
  return (
    <span className={cn(!isActive && "font-medium text-destructive")}>
      {isActive ? "Aktywne" : "Zablokowane"}
    </span>
  );
}

function ApprovalText({ user }: { user: User }) {
  return (
    <span
      className={cn(
        user.approval_status === "approved"
          ? "text-muted-foreground"
          : "font-medium",
      )}
    >
      {approvalLabels[user.approval_status]}
    </span>
  );
}

type FilterButtonsProps = {
  filter: Filter;
  total: number;
  pending: number;
  onChange: (filter: Filter) => void;
};

/** Two-state filter of the teacher list: buttons with aria-pressed. */
function FilterButtons({
  filter,
  total,
  pending,
  onChange,
}: FilterButtonsProps) {
  const options: { value: Filter; label: string }[] = [
    { value: "all", label: `Wszyscy (${total})` },
    { value: "pending", label: `Czekające (${pending})` },
  ];
  return (
    <div role="group" aria-label="Pokaż konta" className="flex gap-1">
      {options.map((option) => (
        <Button
          key={option.value}
          variant={filter === option.value ? "secondary" : "ghost"}
          aria-pressed={filter === option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  );
}

export function UsersTable({ role }: { role: ManagedRole }) {
  const { data: users, isPending, isError, refetch } = useUsers(role);
  const updateUser = useUpdateUser();
  const decide = useDecideApproval();
  const [formTarget, setFormTarget] = useState<FormTarget | null>(null);
  const [blockTarget, setBlockTarget] = useState<User | null>(null);
  const [rejectTarget, setRejectTarget] = useState<User | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const isTeachers = role === "teacher";

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

  const pendingUsers = users.filter(
    (user) => user.approval_status === "pending",
  );
  const showPending = isTeachers && filter === "pending";
  const shown = showPending ? pendingUsers : users;

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

  function decideApproval(user: User, approve: boolean) {
    decide.mutate(
      { id: user.id, approve },
      {
        onSuccess: (updated) => {
          toast.success(
            approve
              ? `Zatwierdzono konto nauczyciela: ${updated.display_name}.`
              : `Odrzucono konto nauczyciela: ${updated.display_name}.`,
          );
          setRejectTarget(null);
        },
        onError: (error) => toast.error(errorMessage(error)),
      },
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {isTeachers ? (
          <FilterButtons
            filter={filter}
            total={users.length}
            pending={pendingUsers.length}
            onChange={setFilter}
          />
        ) : (
          <p className="text-sm text-muted-foreground">
            Liczba kont: {users.length}
          </p>
        )}
        <Button onClick={() => setFormTarget({ role })}>
          <PlusIcon data-icon="inline-start" />
          {texts[role].add}
        </Button>
      </div>

      {shown.length === 0 ? (
        <p className="py-12 text-center text-muted-foreground">
          {showPending
            ? "Żadne konto nauczyciela nie czeka na zatwierdzenie."
            : texts[role].empty}
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Imię</TableHead>
              <TableHead>E-mail</TableHead>
              {isTeachers && <TableHead>Konto</TableHead>}
              <TableHead>Dostęp</TableHead>
              <TableHead>Założone</TableHead>
              <TableHead className="text-right">Akcje</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {shown.map((user) => (
              <TableRow key={user.id}>
                <TableCell className="font-medium">
                  {user.display_name}
                </TableCell>
                <TableCell>{user.email}</TableCell>
                {isTeachers && (
                  <TableCell>
                    {/* The decision sits next to the state it changes */}
                    <div className="flex flex-col items-start gap-1.5 py-1">
                      <ApprovalText user={user} />
                      {user.approval_status !== "approved" && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            disabled={decide.isPending}
                            onClick={() => decideApproval(user, true)}
                            aria-label={`Zatwierdź konto: ${user.display_name}`}
                          >
                            Zatwierdź
                          </Button>
                          {user.approval_status === "pending" && (
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={decide.isPending}
                              onClick={() => setRejectTarget(user)}
                              aria-label={`Odrzuć konto: ${user.display_name}`}
                            >
                              Odrzuć
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  </TableCell>
                )}
                <TableCell>
                  <StatusText isActive={user.is_active} />
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
        open={rejectTarget !== null}
        onOpenChange={(open) => {
          if (!open) {
            setRejectTarget(null);
          }
        }}
      >
        <AlertDialogContent>
          {rejectTarget && (
            <>
              <AlertDialogHeader>
                <AlertDialogTitle>Odrzucić konto nauczyciela?</AlertDialogTitle>
                <AlertDialogDescription>
                  {rejectTarget.display_name} ({rejectTarget.email}) nie utworzy
                  kursów, a po zalogowaniu zobaczy, że konto nie zostało
                  zatwierdzone. Możesz je zatwierdzić później.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Anuluj</AlertDialogCancel>
                <AlertDialogAction
                  variant="destructive"
                  disabled={decide.isPending}
                  onClick={() => decideApproval(rejectTarget, false)}
                >
                  {decide.isPending && <Spinner data-icon="inline-start" />}
                  Odrzuć konto
                </AlertDialogAction>
              </AlertDialogFooter>
            </>
          )}
        </AlertDialogContent>
      </AlertDialog>

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
