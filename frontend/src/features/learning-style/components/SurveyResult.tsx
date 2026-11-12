"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import type { Form } from "@/features/content/types";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group";
import { Spinner } from "@/shared/ui/spinner";

import { learningStyleError } from "../errors";
import {
  PASS_THRESHOLD,
  STEP,
  STYLE_DESCRIPTIONS,
  formLabel,
  pointsText,
  styleName,
} from "../explain";
import { useChooseTiedStyle, useLearningProfile } from "../hooks";
import type { LearningProfile } from "../types";
import { StyleBars } from "./StyleBars";

/** R1: a tie of the survey - the student picks one of the tied styles. */
function TieChoice({ ties }: { ties: Form[] }) {
  const [picked, setPicked] = useState<Form | null>(null);
  const choose = useChooseTiedStyle();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (picked) {
      choose.mutate(picked);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1">
        <h2 id="tie-title" className="text-xl font-semibold">
          Wybierz jeden styl
        </h2>
        <p className="text-muted-foreground">
          {ties.map(formLabel).join(" i ")} mają tyle samo punktów. System uczy
          w jednym stylu naraz – wybierz ten, który bardziej do Ciebie pasuje.
          Wyniki quizów pokażą, czy to dobry wybór.
        </p>
      </div>
      <RadioGroup
        aria-labelledby="tie-title"
        value={picked}
        onValueChange={(value) => setPicked(value as Form)}
      >
        {ties.map((form) => (
          <label
            key={form}
            className={cn(
              "flex min-h-control cursor-pointer items-start gap-3 rounded-lg border px-3 py-3 text-sm transition-colors hover:bg-muted/50",
              picked === form && "border-primary bg-primary/5",
            )}
          >
            <RadioGroupItem value={form} className="mt-0.5" />
            <span>
              <span className="font-medium">{formLabel(form)}</span>
              <span className="block text-muted-foreground">
                {STYLE_DESCRIPTIONS[form]}
              </span>
            </span>
          </label>
        ))}
      </RadioGroup>
      {choose.isError && (
        <p role="alert" className="text-sm text-destructive">
          {learningStyleError(choose.error)}
        </p>
      )}
      <Button type="submit" disabled={!picked || choose.isPending}>
        {choose.isPending && <Spinner data-icon="inline-start" />}
        Wybieram ten styl
      </Button>
    </form>
  );
}

function HowItWorks() {
  return (
    <section aria-labelledby="how-title" className="space-y-2">
      <h2 id="how-title" className="text-xl font-semibold">
        Co dalej
      </h2>
      <ul className="max-w-[65ch] list-disc space-y-1.5 pl-5 text-muted-foreground">
        <li>
          Każda lekcja ma trzy wersje: wzrokową, słuchową i kinestetyczną.
          Dostajesz wersję w formie swojego stylu, a w każdej lekcji możesz
          przełączyć się na inną.
        </li>
        <li>
          Procenty zmieniają się po quizach: pierwsze podejście w danej formie w
          lekcji to +{STEP} punktów za zaliczenie (od {PASS_THRESHOLD}%) albo −
          {STEP} za niezaliczenie.
        </li>
        <li>
          Gdy inna forma okaże się lepsza i potwierdzona wynikami, system
          zaproponuje zmianę stylu – decyzja należy do Ciebie.
        </li>
      </ul>
    </section>
  );
}

function Result({ profile }: { profile: LearningProfile }) {
  const survey = profile.survey!;
  const tie = profile.style === null && profile.tie_styles.length > 0;

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <p className="text-sm text-muted-foreground">Twój wynik ankiety VAK</p>
        <h1 className="text-2xl font-semibold tracking-tight">
          {profile.style
            ? `Twój styl: ${styleName(profile.style)}`
            : "Remis w ankiecie"}
        </h1>
        {profile.style && (
          <p className="max-w-[65ch] text-lg text-muted-foreground">
            {STYLE_DESCRIPTIONS[profile.style]}
          </p>
        )}
      </div>

      <section aria-labelledby="survey-percentages" className="space-y-3">
        <h2 id="survey-percentages" className="text-xl font-semibold">
          Procenty z ankiety
        </h2>
        <StyleBars
          values={survey.percentages}
          label="Procenty form z ankiety"
        />
        <p className="text-sm text-muted-foreground tabular-nums">
          Punkty: {pointsText(survey.points)}. Każda odpowiedź dała jeden punkt
          jednej formie; każda forma ma co najmniej 5%.
        </p>
      </section>

      {tie ? (
        <TieChoice ties={profile.tie_styles} />
      ) : (
        <>
          <HowItWorks />
          <div className="flex flex-wrap gap-3">
            <Link
              href="/courses"
              className={cn(buttonVariants({ size: "lg" }))}
            >
              Przejdź do kursów
            </Link>
            <Link
              href="/profile"
              className={cn(buttonVariants({ size: "lg", variant: "outline" }))}
            >
              Mój styl
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

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
        description={learningStyleError(profile.error)}
        action={
          <Button onClick={() => profile.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }
  if (!profile.data.survey) {
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
  return <Result profile={profile.data} />;
}
