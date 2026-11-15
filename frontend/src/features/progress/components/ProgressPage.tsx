"use client";

import { CloudOffIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { CourseProgressBar } from "@/features/courses/components/CourseProgressBar";
import { AttentionNote } from "@/features/learning-style/components/AttentionNote";
import { useLearningProfile } from "@/features/learning-style/hooks";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import {
  useMyJournal,
  useMyProgress,
  useMyReviewQuestions,
  useMyStats,
} from "../hooks";
import { lessonNumbers } from "../chart-data";
import type { CourseProgress } from "../types";
import { DecisionJournal } from "./DecisionJournal";
import { FormTable } from "./FormTable";
import { LessonResultsTable } from "./LessonResultsTable";
import { PercentChart } from "./PercentChart";
import { ReviewQuestions } from "./ReviewQuestions";
import { StatsSummary } from "./StatsSummary";

function Section({
  id,
  title,
  description,
  children,
}: {
  id: string;
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section aria-labelledby={id} className="space-y-4">
      <div className="space-y-1">
        <h2 id={id} className="text-xl font-semibold">
          {title}
        </h2>
        {description && (
          <p className="max-w-[65ch] text-muted-foreground">{description}</p>
        )}
      </div>
      {children}
    </section>
  );
}

/** Loading and error of one section; the rest of the page stays usable. */
function SectionQuery<T>({
  query,
  errorText,
  children,
}: {
  query: {
    isPending: boolean;
    isError: boolean;
    data: T | undefined;
    refetch: () => unknown;
  };
  errorText: string;
  children: (data: T) => ReactNode;
}) {
  if (query.isPending) {
    return (
      <div className="flex justify-center py-6">
        <Spinner className="size-5" />
      </div>
    );
  }
  if (query.isError || query.data === undefined) {
    return (
      <div className="space-y-3">
        <p role="alert" className="text-sm text-destructive">
          {errorText}
        </p>
        <Button variant="outline" onClick={() => query.refetch()}>
          Spróbuj ponownie
        </Button>
      </div>
    );
  }
  return <>{children(query.data)}</>;
}

function Courses({ courses }: { courses: CourseProgress[] }) {
  if (courses.length === 0) {
    return (
      <p className="text-muted-foreground">
        Nie masz jeszcze żadnego kursu.{" "}
        <Link
          href="/courses"
          className="font-medium underline underline-offset-4"
        >
          Zobacz katalog
        </Link>
      </p>
    );
  }
  return (
    <ul role="list" className="divide-y border-y">
      {courses.map((course) => (
        <li
          key={course.id}
          className="grid gap-3 py-4 sm:grid-cols-[minmax(0,1fr)_16rem] sm:items-center sm:gap-8"
        >
          <div className="min-w-0 space-y-0.5">
            <Link
              href={`/courses/${course.id}`}
              className="font-medium underline-offset-4 hover:underline"
            >
              {course.title}
            </Link>
            <p className="text-sm text-muted-foreground">
              {course.next_lesson ? (
                <>
                  Następna:{" "}
                  <Link
                    href={`/courses/${course.id}/lessons/${course.next_lesson.id}`}
                    className="underline underline-offset-4 hover:text-foreground"
                  >
                    Lekcja {course.next_lesson.number}:{" "}
                    {course.next_lesson.title}
                  </Link>
                </>
              ) : course.total > 0 && course.passed >= course.total ? (
                "Kurs ukończony"
              ) : (
                "Brak kolejnej lekcji"
              )}
            </p>
          </div>
          <CourseProgressBar passed={course.passed} total={course.total} />
        </li>
      ))}
    </ul>
  );
}

/** "Moje postępy": percentages over time, courses, results and the journal. */
export function ProgressPage() {
  const progress = useMyProgress();
  const journal = useMyJournal();
  const stats = useMyStats();
  const review = useMyReviewQuestions();
  const profile = useLearningProfile();

  if (progress.isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (progress.isError) {
    return (
      <PageMessage
        icon={CloudOffIcon}
        title="Nie udało się wczytać postępów"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={
          <Button onClick={() => progress.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }

  const data = progress.data;

  return (
    <div className="space-y-12">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Moje postępy</h1>
        <p className="max-w-[65ch] text-muted-foreground">
          Jak zmieniały się procenty form, ile lekcji masz za sobą i każda
          decyzja systemu z liczbami, z których wynika.
        </p>
      </div>

      {stats.data?.attention && (
        <AttentionNote attention={stats.data.attention} />
      )}

      <Section
        id="summary"
        title="Podsumowanie"
        description="Średni wynik i seria liczą tylko pierwsze podejście do lekcji w danej formie, bez powtórek."
      >
        <SectionQuery
          query={stats}
          errorText="Nie udało się wczytać podsumowania."
        >
          {(data) => <StatsSummary summary={data.summary} />}
        </SectionQuery>
      </Section>

      <Section
        id="forms"
        title="W której formie idzie Ci najlepiej"
        description="Jeden wiersz to jedna forma, liczby ze wszystkich Twoich kursów. „Za pierwszym razem” i „Średnia” liczą pierwsze podejście do lekcji w tej formie; procent zaliczeń pojawia się od 2 lekcji."
      >
        <SectionQuery
          query={stats}
          errorText="Nie udało się wczytać tabeli form."
        >
          {(data) => (
            <FormTable forms={data.forms} style={profile.data?.style ?? null} />
          )}
        </SectionQuery>
      </Section>

      <Section
        id="review"
        title="Do powtórki"
        description="Pytania, na które w ostatnim podejściu do lekcji padła zła odpowiedź. Najnowsze są na górze, najwyżej 5."
      >
        <SectionQuery
          query={review}
          errorText="Nie udało się wczytać pytań do powtórki."
        >
          {(questions) => <ReviewQuestions questions={questions} />}
        </SectionQuery>
      </Section>

      <Section
        id="chart"
        title="Procenty form w czasie"
        description="Procenty startują z ankiety i zmieniają się po każdym policzonym quizie. Zmiana stylu nie zmienia procentów, na wykresie jest pionową linią."
      >
        <PercentChart
          history={data.history}
          lessonNumbers={lessonNumbers(data.lessons)}
        />
      </Section>

      <Section id="courses" title="Kursy">
        <Courses courses={data.courses} />
      </Section>

      <Section
        id="results"
        title="Wyniki lekcji"
        description="Tu jest każde podejście do quizu. Procenty zmienia tylko pierwsze podejście do lekcji w danej formie."
      >
        <LessonResultsTable lessons={data.lessons} />
      </Section>

      <Section
        id="journal"
        title="Dziennik decyzji"
        description="Najnowsze wpisy są na górze. Przy każdej reakcji systemu są liczby, z których wynika."
      >
        {journal.isPending ? (
          <div className="flex justify-center py-6">
            <Spinner className="size-5" />
          </div>
        ) : journal.isError ? (
          <div className="space-y-3">
            <p role="alert" className="text-sm text-destructive">
              Nie udało się wczytać dziennika.
            </p>
            <Button variant="outline" onClick={() => journal.refetch()}>
              Spróbuj ponownie
            </Button>
          </div>
        ) : (
          <DecisionJournal entries={journal.data} />
        )}
      </Section>
    </div>
  );
}
