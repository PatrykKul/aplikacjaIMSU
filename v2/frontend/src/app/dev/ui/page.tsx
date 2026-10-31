import { AlertCircleIcon } from "lucide-react";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/shared/ui/field";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";
import { FormField } from "@/shared/ui/form-field";
import { PasswordInput } from "@/shared/ui/password-input";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="text-lg font-medium">{title}</h2>
      {children}
    </section>
  );
}

export default function DevUiPage() {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl space-y-12 p-8">
      <h1 className="text-2xl font-semibold">Komponenty</h1>

      <Section title="Przyciski">
        <div className="flex flex-wrap gap-3">
          <Button>Domyślny</Button>
          <Button variant="secondary">Drugorzędny</Button>
          <Button variant="outline">Obrys</Button>
          <Button variant="ghost">Duch</Button>
          <Button variant="destructive">Usuń</Button>
          <Button disabled>Wyłączony</Button>
          <Button disabled>
            <Spinner data-icon="inline-start" />
            Logowanie…
          </Button>
        </div>
      </Section>

      <Section title="Stany pola">
        <FieldGroup className="max-w-sm">
          <Field>
            <FieldLabel htmlFor="field-default">E-mail</FieldLabel>
            <Input
              id="field-default"
              type="email"
              placeholder="jan@przyklad.pl"
            />
          </Field>

          <Field>
            <FieldLabel htmlFor="field-hint">Hasło</FieldLabel>
            <Input
              id="field-hint"
              type="password"
              aria-describedby="field-hint-text"
            />
            <FieldDescription id="field-hint-text">
              Co najmniej 8 znaków.
            </FieldDescription>
          </Field>

          <Field data-invalid>
            <FieldLabel htmlFor="field-error">E-mail</FieldLabel>
            <Input
              id="field-error"
              type="email"
              defaultValue="jan@"
              aria-invalid
              aria-describedby="field-error-text"
            />
            <FieldError id="field-error-text">
              Podaj poprawny adres e-mail, np. jan@przyklad.pl.
            </FieldError>
          </Field>

          <Field data-disabled>
            <FieldLabel htmlFor="field-disabled">Imię</FieldLabel>
            <Input id="field-disabled" defaultValue="Jan" disabled />
          </Field>
        </FieldGroup>
      </Section>

      <Section title="Pole formularza i hasło">
        <FieldGroup className="max-w-sm">
          <FormField label="Hasło" description="Co najmniej 8 znaków.">
            {(control) => (
              <PasswordInput {...control} autoComplete="new-password" />
            )}
          </FormField>
          <FormField
            label="E-mail"
            error="Podaj poprawny adres e-mail, np. jan@przyklad.pl."
          >
            {(control) => (
              <Input {...control} type="email" defaultValue="jan@" />
            )}
          </FormField>
        </FieldGroup>
      </Section>

      <Section title="Komunikat błędu formularza">
        <Alert variant="destructive" className="max-w-sm">
          <AlertCircleIcon />
          <AlertTitle>Nie udało się zalogować</AlertTitle>
          <AlertDescription>
            Nieprawidłowy e-mail lub hasło. Sprawdź dane i spróbuj ponownie.
          </AlertDescription>
        </Alert>
      </Section>

      <Section title="Złożenie: karta logowania (szkic)">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>Zaloguj się</CardTitle>
            <CardDescription>Podaj swój e-mail i hasło.</CardDescription>
          </CardHeader>
          <CardContent>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="login-email">E-mail</FieldLabel>
                <Input id="login-email" type="email" />
              </Field>
              <Field>
                <FieldLabel htmlFor="login-password">Hasło</FieldLabel>
                <Input id="login-password" type="password" />
              </Field>
              <Button className="w-full">Zaloguj się</Button>
            </FieldGroup>
          </CardContent>
        </Card>
      </Section>
    </main>
  );
}
