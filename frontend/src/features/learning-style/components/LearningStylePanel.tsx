"use client";

import Link from "next/link";
import { useState } from "react";

import { FORMS, type Form } from "@/features/content/types";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button, buttonVariants } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Checkbox } from "@/shared/ui/checkbox";
import { Spinner } from "@/shared/ui/spinner";

import { learningStyleError } from "../errors";
import {
  useChangeStyle,
  useLearningProfile,
  useRestoreStyle,
  useSurveyResults,
} from "../hooks";
import {
  SOURCE_LABELS,
  STYLE_DESCRIPTIONS,
  STYLE_NAMES,
  describeStyle,
  joinStyle,
  styleLetters,
} from "../styles";
import type { LearningProfile } from "../types";
import { StyleBars } from "./StyleBars";
import { StyleProposalBanner } from "./StyleProposalBanner";

const WEIGHT_MAX = 30;

function ManualStyle({ profile }: { profile: LearningProfile }) {
  const current = styleLetters(profile.style ?? "");
  const [picked, setPicked] = useState<Form[]>(current);
  const change = useChangeStyle();
  const restore = useRestoreStyle();
  const unchanged = joinStyle(picked) === profile.style;

  function toggle(form: Form) {
    setPicked((prev) =>
      prev.includes(form) ? prev.filter((f) => f !== form) : [...prev, form],
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Zmień styl</CardTitle>
        <CardDescription>
          Zaznacz jeden albo kilka stylów. Wynik ankiety zostaje zapisany, a do
          stylu z ankiety możesz wrócić w każdej chwili.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-2 sm:grid-cols-3">
          {FORMS.map((form) => (
            <label
              key={form}
              className={cn(
                "flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm transition-colors hover:bg-muted/50",
                picked.includes(form) && "border-primary bg-primary/5",
              )}
            >
              <Checkbox
                className="mt-0.5"
                checked={picked.includes(form)}
                onCheckedChange={() => toggle(form)}
              />
              <span>
                <span className="font-medium">
                  {form} · {STYLE_NAMES[form]}
                </span>
                <span className="block text-muted-foreground">
                  {STYLE_DESCRIPTIONS[form]}
                </span>
              </span>
            </label>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            disabled={picked.length === 0 || unchanged || change.isPending}
            onClick={() => change.mutate(joinStyle(picked))}
          >
            Zapisz styl
          </Button>
          {profile.style_source !== "survey" && (
            <Button
              variant="outline"
              disabled={restore.isPending}
              onClick={() =>
                restore.mutate(undefined, {
                  onSuccess: (p) => setPicked(styleLetters(p.style ?? "")),
                })
              }
            >
              Przywróć styl z ankiety
            </Button>
          )}
          <Link
            href="/survey"
            className={cn(buttonVariants({ variant: "ghost" }))}
          >
            Wypełnij ankietę ponownie
          </Link>
        </div>
        {picked.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Wybierz co najmniej jeden styl.
          </p>
        )}
        {(change.error ?? restore.error) && (
          <p role="alert" className="text-sm text-destructive">
            {learningStyleError(change.error ?? restore.error)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function History() {
  const results = useSurveyResults();
  if (!results.data || results.data.length === 0) {
    return null;
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle>Historia ankiet</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="divide-y text-sm">
          {results.data.map((result) => (
            <li
              key={result.created_at}
              className="flex flex-wrap items-center justify-between gap-2 py-2"
            >
              <span>{new Date(result.created_at).toLocaleString("pl-PL")}</span>
              <span className="text-muted-foreground tabular-nums">
                V {result.points.V} / A {result.points.A} / K {result.points.K}
              </span>
              <Badge variant="secondary">
                {describeStyle(result.dominant_style)}
              </Badge>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export function LearningStylePanel() {
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
        title="Nie udało się wczytać Twojego stylu"
        description={learningStyleError(profile.error)}
        action={
          <Button onClick={() => profile.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }

  const data = profile.data;
  if (!data.survey_completed || !data.style || !data.weights) {
    return (
      <PageMessage
        title="Nie znamy jeszcze Twojego stylu"
        action={
          <Link href="/survey" className={cn(buttonVariants())}>
            Wypełnij ankietę
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">
        Mój styl uczenia się
      </h1>

      {data.proposal && <StyleProposalBanner proposal={data.proposal} />}

      <Card>
        <CardHeader>
          <CardDescription>Aktualny styl</CardDescription>
          <CardTitle className="flex flex-wrap items-center gap-2 text-xl">
            {describeStyle(data.style)}
            {data.style_source && (
              <Badge variant="outline">
                {SOURCE_LABELS[data.style_source]}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">
            <span className="font-medium">Dlaczego: </span>
            {data.explanation}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Jak system Cię widzi</CardTitle>
          <CardDescription>
            Wagi stylów startują od punktów z ankiety. Po każdym quizie styl, w
            którym się uczysz, dostaje +1 za zaliczenie (od 70%) albo −1 za
            niezaliczenie. Gdy inny styl wyjdzie na prowadzenie, system
            zaproponuje zmianę, ale decyzja należy do Ciebie.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <StyleBars
            values={data.weights}
            max={WEIGHT_MAX}
            label="Wagi stylów"
          />
        </CardContent>
      </Card>

      <ManualStyle key={data.style} profile={data} />
      <History />
    </div>
  );
}
