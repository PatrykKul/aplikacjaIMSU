"use client";

import { AlertCircleIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import type { ManagedRole, User } from "@/features/auth/types";
import {
  displayNameRules,
  emailRules,
  newPasswordRules,
} from "@/features/auth/validation";
import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
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
import { FieldGroup } from "@/shared/ui/field";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { PasswordInput } from "@/shared/ui/password-input";
import { Spinner } from "@/shared/ui/spinner";

import type { UserUpdateInput } from "../api";
import { useCreateUser, useUpdateUser } from "../hooks";

/** Which form to show: a new account of the role, or editing `user`. */
export type FormTarget = { role: ManagedRole; user?: User };

type FormValues = { display_name: string; email: string; password: string };

const titles: Record<ManagedRole, { create: string; edit: string }> = {
  teacher: { create: "Nowy nauczyciel", edit: "Edycja nauczyciela" },
  student: { create: "Nowy uczeń", edit: "Edycja ucznia" },
};

const optionalPasswordRules = {
  validate: (value: string) => value === "" || newPasswordRules.validate(value),
  minLength: newPasswordRules.minLength,
};

function changedFields(user: User, values: FormValues): UserUpdateInput {
  const changes: UserUpdateInput = {};
  if (values.display_name.trim() !== user.display_name) {
    changes.display_name = values.display_name;
  }
  if (values.email.trim().toLowerCase() !== user.email) {
    changes.email = values.email;
  }
  if (values.password !== "") {
    changes.password = values.password;
  }
  return changes;
}

type UserFormDialogProps = {
  target: FormTarget | null;
  onClose: () => void;
};

export function UserFormDialog({ target, onClose }: UserFormDialogProps) {
  const user = target?.user;
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const mutation = user ? updateUser : createUser;
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues: {
      display_name: user?.display_name ?? "",
      email: user?.email ?? "",
      password: "",
    },
  });

  function handleError(error: Error) {
    if (error instanceof ApiError && error.code === "EMAIL_TAKEN") {
      setError("email", { message: "Ten adres e-mail jest już zajęty." });
    }
  }

  const onSubmit = handleSubmit((values) => {
    if (!target) {
      return;
    }
    if (!user) {
      createUser.mutate(
        { ...values, role: target.role },
        {
          onSuccess: (created) => {
            toast.success(`Dodano konto: ${created.display_name}.`);
            onClose();
          },
          onError: handleError,
        },
      );
      return;
    }
    const changes = changedFields(user, values);
    if (Object.keys(changes).length === 0) {
      onClose();
      return;
    }
    updateUser.mutate(
      { id: user.id, data: changes },
      {
        onSuccess: (updated) => {
          toast.success(`Zapisano zmiany: ${updated.display_name}.`);
          onClose();
        },
        onError: handleError,
      },
    );
  });

  const showAlert =
    mutation.isError &&
    !(
      mutation.error instanceof ApiError &&
      mutation.error.code === "EMAIL_TAKEN"
    );

  return (
    <Dialog
      open={target !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent>
        {target && (
          <form onSubmit={onSubmit} noValidate className="grid gap-4">
            <DialogHeader>
              <DialogTitle>
                {user ? titles[target.role].edit : titles[target.role].create}
              </DialogTitle>
              <DialogDescription>
                {user
                  ? "Zmień dane konta. Rola konta się nie zmienia."
                  : "Przekaż tej osobie e-mail i hasło — zaloguje się nimi."}
              </DialogDescription>
            </DialogHeader>

            <FieldGroup>
              {showAlert && (
                <Alert variant="destructive">
                  <AlertCircleIcon />
                  <AlertTitle>Nie udało się zapisać</AlertTitle>
                  <AlertDescription>
                    {errorMessage(mutation.error)}
                  </AlertDescription>
                </Alert>
              )}
              <FormField label="Imię" error={errors.display_name?.message}>
                {(control) => (
                  <Input
                    {...control}
                    autoComplete="off"
                    {...register("display_name", displayNameRules)}
                  />
                )}
              </FormField>
              <FormField label="E-mail" error={errors.email?.message}>
                {(control) => (
                  <Input
                    {...control}
                    type="email"
                    autoComplete="off"
                    {...register("email", emailRules)}
                  />
                )}
              </FormField>
              <FormField
                label={user ? "Nowe hasło" : "Hasło"}
                description={
                  user
                    ? "Zostaw puste, żeby nie zmieniać hasła."
                    : "Co najmniej 8 znaków."
                }
                error={errors.password?.message}
              >
                {(control) => (
                  <PasswordInput
                    {...control}
                    autoComplete="new-password"
                    {...register(
                      "password",
                      user ? optionalPasswordRules : newPasswordRules,
                    )}
                  />
                )}
              </FormField>
            </FieldGroup>

            <DialogFooter>
              <DialogClose render={<Button type="button" variant="outline" />}>
                Anuluj
              </DialogClose>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending && <Spinner data-icon="inline-start" />}
                {user ? "Zapisz zmiany" : "Dodaj konto"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
