"use client";

import { useState } from "react";
import { toast } from "sonner";

import { useCurrentUser } from "@/features/auth/hooks";
import { roleLabels } from "@/features/auth/roles";
import type { User, UserRole } from "@/features/auth/types";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
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

const roleItems = (Object.keys(roleLabels) as UserRole[]).map((role) => ({
  value: role,
  label: roleLabels[role],
}));

export function UsersTable() {
  const { data: currentUser } = useCurrentUser();
  const { data: users, isPending, isError, refetch } = useUsers();
  const updateUser = useUpdateUser();
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
        title="Nie udało się wczytać użytkowników"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  function changeRole(user: User, role: UserRole) {
    updateUser.mutate(
      { id: user.id, data: { role } },
      {
        onSuccess: () =>
          toast.success(
            `Zmieniono rolę: ${user.display_name} - ${roleLabels[role]}.`,
          ),
        onError: (error) => toast.error(errorMessage(error)),
      },
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
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">
        Użytkownicy{" "}
        <span className="font-normal text-muted-foreground">
          ({users.length})
        </span>
      </h1>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Imię</TableHead>
            <TableHead>E-mail</TableHead>
            <TableHead>Rola</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Akcja</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {users.map((user) => {
            const isSelf = user.id === currentUser?.id;
            return (
              <TableRow key={user.id}>
                <TableCell className="font-medium">
                  {user.display_name}
                  {isSelf && (
                    <span className="text-muted-foreground"> (Ty)</span>
                  )}
                </TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  {isSelf ? (
                    roleLabels[user.role]
                  ) : (
                    <Select
                      items={roleItems}
                      value={user.role}
                      onValueChange={(value) => {
                        if (value && value !== user.role) {
                          changeRole(user, value as UserRole);
                        }
                      }}
                    >
                      <SelectTrigger
                        className="w-40"
                        aria-label={`Rola: ${user.display_name}`}
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {roleItems.map((item) => (
                          <SelectItem key={item.value} value={item.value}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </TableCell>
                <TableCell>
                  <Badge variant={user.is_active ? "secondary" : "destructive"}>
                    {user.is_active ? "Aktywny" : "Zablokowany"}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  {isSelf ? (
                    <span className="text-muted-foreground">—</span>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setBlockTarget(user)}
                    >
                      {user.is_active ? "Zablokuj" : "Odblokuj"}
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

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
