"use client";

import { AlertCircleIcon, BackpackIcon, PresentationIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";

import { errorMessage } from "@/shared/api/error-messages";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { FieldGroup } from "@/shared/ui/field";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { PasswordInput } from "@/shared/ui/password-input";
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group";
import { Spinner } from "@/shared/ui/spinner";

import { useRegister } from "../hooks";
import type { ManagedRole, RegisterInput } from "../types";
import { displayNameRules, emailRules, newPasswordRules } from "../validation";

const roleOptions = [
  {
    value: "student",
    label: "Uczniem",
    description: "Uczę się z kursów",
    icon: BackpackIcon,
  },
  {
    value: "teacher",
    label: "Nauczycielem",
    description: "Prowadzę zajęcia",
    icon: PresentationIcon,
  },
] as const;

export function RegisterForm() {
  const router = useRouter();
  const registerUser = useRegister();
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterInput>({
    defaultValues: {
      role: "student",
      display_name: "",
      email: "",
      password: "",
    },
  });

  const onSubmit = handleSubmit((data) =>
    registerUser.mutate(data, {
      onSuccess: () => router.replace("/dashboard"),
    }),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Załóż konto</CardTitle>
        <CardDescription>To zajmie tylko chwilę.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} noValidate>
          <FieldGroup>
            {registerUser.isError && (
              <Alert variant="destructive">
                <AlertCircleIcon />
                <AlertTitle>Nie udało się założyć konta</AlertTitle>
                <AlertDescription>
                  {errorMessage(registerUser.error)}
                </AlertDescription>
              </Alert>
            )}

            <fieldset>
              <legend id="register-role" className="mb-3 text-sm font-medium">
                Kim jesteś?
              </legend>
              <Controller
                control={control}
                name="role"
                render={({ field }) => (
                  <RadioGroup
                    aria-labelledby="register-role"
                    value={field.value}
                    onValueChange={(value) =>
                      field.onChange(value as ManagedRole)
                    }
                    className="grid-cols-2 gap-3"
                  >
                    {roleOptions.map(
                      ({ value, label, description, icon: Icon }) => (
                        <label
                          key={value}
                          className="group relative flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 p-4 text-center transition-colors not-has-data-checked:hover:bg-muted has-focus-visible:ring-3 has-focus-visible:ring-ring/50 has-data-checked:border-primary has-data-checked:bg-accent"
                        >
                          <RadioGroupItem
                            value={value}
                            className="absolute top-3 right-3"
                          />
                          <Icon
                            className="size-8 text-muted-foreground transition-colors group-has-data-checked:text-primary"
                            aria-hidden
                          />
                          <span className="text-sm font-medium">{label}</span>
                          <span className="text-xs text-muted-foreground">
                            {description}
                          </span>
                        </label>
                      ),
                    )}
                  </RadioGroup>
                )}
              />
            </fieldset>

            <FormField label="Imię" error={errors.display_name?.message}>
              {(control) => (
                <Input
                  {...control}
                  autoComplete="given-name"
                  {...register("display_name", displayNameRules)}
                />
              )}
            </FormField>
            <FormField label="E-mail" error={errors.email?.message}>
              {(control) => (
                <Input
                  {...control}
                  type="email"
                  autoComplete="email"
                  {...register("email", emailRules)}
                />
              )}
            </FormField>
            <FormField
              label="Hasło"
              description="Co najmniej 8 znaków."
              error={errors.password?.message}
            >
              {(control) => (
                <PasswordInput
                  {...control}
                  autoComplete="new-password"
                  {...register("password", newPasswordRules)}
                />
              )}
            </FormField>

            <Button
              type="submit"
              className="w-full"
              disabled={registerUser.isPending}
            >
              {registerUser.isPending && <Spinner data-icon="inline-start" />}
              {registerUser.isPending ? "Zakładanie konta..." : "Załóż konto"}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
      <CardFooter className="justify-center">
        <p className="text-sm text-muted-foreground">
          Masz już konto?{" "}
          <Link
            href="/login"
            className="font-medium text-foreground underline underline-offset-4"
          >
            Zaloguj się
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
