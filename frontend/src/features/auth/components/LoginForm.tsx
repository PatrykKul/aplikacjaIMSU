"use client";

import { AlertCircleIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

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
import { Spinner } from "@/shared/ui/spinner";

import { useLogin } from "../hooks";
import type { LoginInput } from "../types";
import { emailRules, loginPasswordRules } from "../validation";

export function LoginForm() {
  const router = useRouter();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({ defaultValues: { email: "", password: "" } });

  const onSubmit = handleSubmit((data) =>
    login.mutate(data, { onSuccess: () => router.replace("/dashboard") }),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Zaloguj się</CardTitle>
        <CardDescription>Podaj swój e-mail i hasło.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} noValidate>
          <FieldGroup>
            {login.isError && (
              <Alert variant="destructive">
                <AlertCircleIcon />
                <AlertTitle>Nie udało się zalogować</AlertTitle>
                <AlertDescription>{errorMessage(login.error)}</AlertDescription>
              </Alert>
            )}
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
            <FormField label="Hasło" error={errors.password?.message}>
              {(control) => (
                <PasswordInput
                  {...control}
                  autoComplete="current-password"
                  {...register("password", loginPasswordRules)}
                />
              )}
            </FormField>
            <Button type="submit" className="w-full" disabled={login.isPending}>
              {login.isPending && <Spinner data-icon="inline-start" />}
              {login.isPending ? "Logowanie..." : "Zaloguj się"}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
      <CardFooter className="justify-center">
        <p className="text-sm text-muted-foreground">
          Nie masz konta?{" "}
          <Link
            href="/register"
            className="font-medium text-foreground underline underline-offset-4"
          >
            Załóż konto
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
