import Link from "next/link";

import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Field, FieldGroup, FieldLabel } from "@/shared/ui/field";
import { Input } from "@/shared/ui/input";

export default function LoginPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Zaloguj się</CardTitle>
        <CardDescription>Podaj swój e-mail i hasło.</CardDescription>
      </CardHeader>
      <CardContent>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="email">E-mail</FieldLabel>
            <Input id="email" type="email" autoComplete="email" />
          </Field>
          <Field>
            <FieldLabel htmlFor="password">Hasło</FieldLabel>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
            />
          </Field>
          <Button className="w-full">Zaloguj się</Button>
        </FieldGroup>
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
