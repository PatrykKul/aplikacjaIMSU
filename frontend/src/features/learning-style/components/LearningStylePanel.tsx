"use client";

import { ClipboardListIcon, CloudOffIcon } from "lucide-react";
import Link from "next/link";
import { type FormEvent, useState } from "react";
import { toast } from "sonner";

import { FORMS, type Form } from "@/features/content/types";
import { FormPercentages } from "@/features/progress/components/FormPercentages";
import { formatDateTime } from "@/features/progress/format";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { Button, buttonVariants } from "@/shared/ui/button";
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group";
import { Spinner } from "@/shared/ui/spinner";

import { learningStyleError } from "../errors";
import {
  PASS_THRESHOLD,
  STEP,
  STYLE_DESCRIPTIONS,
  TRIAL_LESSONS,
  formLabel,
  lessonsText,
  pointsText,
  styleName,
  styleSourceText,
} from "../explain";
import { useChangeStyle, useLearningProfile } from "../hooks";
import type { LearningProfile } from "../types";
import { StyleBars } from "./StyleBars";
import { StyleProposalBanner } from "./StyleProposalBanner";
import { TrialNote } from "./TrialNote";

/** Manual change of the style: RadioGroup + confirmation (percentages stay). */
function ManualStyle({ profile }: { profile: LearningProfile }) {
  const [picked, setPicked] = useState<Form | null>(profile.style);
  const [confirming, setConfirming] = useState(false);
  const change = useChangeStyle();
  const unchanged = picked === profile.style;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (picked && !unchanged) {
      setConfirming(true);
    }
  }

  function confirm() {
    if (!picked) {
      return;
    }
    change.mutate(picked, {
      onSuccess: () => {
        setConfirming(false);
        toast.success(`Twój styl: ${styleName(picked)}`);
      },
    });
  }

  return (
    <section aria-labelledby="manual-style" className="space-y-4">
      <div className="space-y-1">
        <h2 id="manual-style" className="text-xl font-semibold">
          Zmień styl
        </h2>
        <p className="max-w-[65ch] text-muted-foreground">
          Styl możesz też wybrać samodzielnie. Procenty się przy tym nie
          zmienią, zmieniają je tylko wyniki quizów.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <RadioGroup
          aria-labelledby="manual-style"
          value={picked}
          onValueChange={(value) => setPicked(value as Form)}
          className="sm:grid-cols-3"
        >
          {FORMS.map((form) => (
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
                {form === profile.style && (
                  <span className="text-muted-foreground"> · obecny</span>
                )}
                <span className="block text-muted-foreground">
                  {STYLE_DESCRIPTIONS[form]}
                </span>
              </span>
            </label>
          ))}
        </RadioGroup>
        <Button type="submit" disabled={!picked || unchanged}>
          Zmień styl
        </Button>
      </form>

      <AlertDialog
        open={confirming}
        onOpenChange={(open) => {
          if (!change.isPending) {
            setConfirming(open);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {picked
                ? `Zmienić styl na ${styleName(picked)}?`
                : "Zmienić styl?"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              Procenty się nie zmienią, a zmiana trafi do dziennika. Lekcje,
              które nie są jeszcze zaliczone, dostaniesz w nowej formie. Przez{" "}
              {lessonsText(TRIAL_LESSONS)} potrwa okres próbny, po nim
              zobaczysz, czy zmiana pomogła.
              {profile.open_proposal &&
                " Otwarta propozycja systemu zostanie zamknięta."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          {change.isError && (
            <p role="alert" className="text-sm text-destructive">
              {learningStyleError(change.error)}
            </p>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel disabled={change.isPending}>
              Anuluj
            </AlertDialogCancel>
            <Button disabled={change.isPending} onClick={confirm}>
              {change.isPending && <Spinner data-icon="inline-start" />}
              Zmień styl
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
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
        icon={CloudOffIcon}
        title="Nie udało się wczytać Twojego stylu"
        description={learningStyleError(profile.error)}
        action={
          <Button onClick={() => profile.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }

  const data = profile.data;
  if (!data.survey_completed || !data.style) {
    return (
      <PageMessage
        icon={ClipboardListIcon}
        title="Nie znamy jeszcze Twojego stylu"
        description={
          data.survey_completed
            ? "Ankieta dała remis. Wybierz jeden styl."
            : "Wypełnij ankietę. To 20 krótkich pytań."
        }
        action={
          <Link
            href={data.survey_completed ? "/survey/result" : "/survey"}
            className={cn(buttonVariants())}
          >
            {data.survey_completed ? "Wybierz styl" : "Wypełnij ankietę"}
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-10">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Mój styl uczenia się
        </h1>
        <p className="text-lg">
          Twój styl:{" "}
          <strong className="font-semibold">{styleName(data.style)}</strong>
          {data.style_source && (
            <span className="text-muted-foreground">
              , {styleSourceText(data.style_source)}
            </span>
          )}
        </p>
        <p className="max-w-[65ch] text-muted-foreground">
          {STYLE_DESCRIPTIONS[data.style]} Lekcje dostajesz w tej formie, chyba
          że dla danej lekcji wybierzesz inną.
        </p>
      </div>

      {data.open_proposal && (
        <StyleProposalBanner proposal={data.open_proposal} />
      )}

      {data.trial && <TrialNote trial={data.trial} showRule />}

      <section aria-labelledby="form-percentages" className="space-y-3">
        <div className="space-y-1">
          <h2 id="form-percentages" className="text-xl font-semibold">
            Procenty form
          </h2>
          <p className="max-w-[65ch] text-muted-foreground">
            Procenty startują z ankiety, potem zmieniają je tylko wyniki quizów.
            Liczy się pierwsze podejście do lekcji w danej formie: zaliczenie
            (od {PASS_THRESHOLD}%) daje tej formie +{STEP} punktów,
            niezaliczenie −{STEP}. Pozostałe dwie formy oddają albo dostają te
            punkty tak, żeby suma zawsze wynosiła 100%. Forma jest potwierdzona
            wynikami, gdy masz w niej co najmniej jeden zaliczony quiz.
          </p>
        </div>
        <FormPercentages profile={data} />
        <Link
          href="/progress"
          className="inline-block text-sm font-medium underline underline-offset-4"
        >
          Wykres i dziennik decyzji w „Moich postępach”
        </Link>
      </section>

      <ManualStyle key={data.style} profile={data} />

      {data.survey && (
        <section aria-labelledby="survey-result" className="space-y-3">
          <div className="space-y-1">
            <h2 id="survey-result" className="text-xl font-semibold">
              Wynik ankiety
            </h2>
            <p className="text-sm text-muted-foreground">
              Wypełniona {formatDateTime(data.survey.created_at)} · punkty:{" "}
              {pointsText(data.survey.points)}
            </p>
          </div>
          <StyleBars
            values={data.survey.percentages}
            label="Procenty form z ankiety"
          />
        </section>
      )}
    </div>
  );
}
