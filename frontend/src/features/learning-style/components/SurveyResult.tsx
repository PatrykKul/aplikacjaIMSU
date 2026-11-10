"use client";

import Link from "next/link";

import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Spinner } from "@/shared/ui/spinner";

import { useLearningProfile } from "../hooks";
import { STYLE_DESCRIPTIONS, describeStyle, styleLetters } from "../styles";
import { StyleBars } from "./StyleBars";

export function SurveyResult() {
  const profile = useLearningProfile();

  if (profile.isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (profile.isError) {
    return (
      <PageMessage
        title="Nie udało się wczytać wyniku"
        action={
          <Button onClick={() => profile.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }
  const result = profile.data.last_result;
  if (!result) {
    return (
      <PageMessage
        title="Nie masz jeszcze wyniku"
        description="Wypełnij ankietę, żeby poznać swój styl uczenia się."
        action={
          <Link href="/survey" className={cn(buttonVariants())}>
            Przejdź do ankiety
          </Link>
        }
      />
    );
  }

  const letters = styleLetters(result.dominant_style);
  const total = result.points.V + result.points.A + result.points.K;

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">Twój wynik ankiety VAK</p>
        <h1 className="text-2xl font-semibold tracking-tight">
          Twój styl: {describeStyle(result.dominant_style)}
        </h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Co to znaczy</CardTitle>
          <CardDescription>
            {letters.length > 1
              ? "Remis w ankiecie: dostaniesz materiały dla każdego z tych stylów."
              : "Materiały w lekcjach zostaną dobrane do tego stylu."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {letters.map((form) => (
              <li key={form}>
                <strong>{form}</strong> – {STYLE_DESCRIPTIONS[form]}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Punkty z ankiety</CardTitle>
          <CardDescription>
            Każda odpowiedź dała jeden punkt jednemu stylowi.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <StyleBars
            values={result.points}
            max={total}
            label="Punkty z ankiety"
          />
        </CardContent>
      </Card>

      <p className="text-sm text-muted-foreground">
        Styl możesz w każdej chwili zmienić w zakładce „Mój styl”. System
        podpowie też zmianę, jeśli wyniki quizów pokażą, że lepiej idzie Ci z
        innymi materiałami.
      </p>

      <div className="flex flex-wrap gap-3">
        <Link href="/courses" className={cn(buttonVariants({ size: "lg" }))}>
          Przejdź do kursów
        </Link>
        <Link
          href="/profile"
          className={cn(buttonVariants({ size: "lg", variant: "outline" }))}
        >
          Mój styl uczenia się
        </Link>
      </div>
    </div>
  );
}
