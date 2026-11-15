"use client";

import { CloudOffIcon, SearchXIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import {
  attentionSeries,
  profileSummaryLines,
} from "@/features/learning-style/explain";
import type {
  Attention,
  LearningProfile,
} from "@/features/learning-style/types";
import { lessonNumbers } from "@/features/progress/chart-data";
import { DecisionJournal } from "@/features/progress/components/DecisionJournal";
import { FormPercentages } from "@/features/progress/components/FormPercentages";
import { FormTable } from "@/features/progress/components/FormTable";
import { LessonResultsTable } from "@/features/progress/components/LessonResultsTable";
import { PercentChart } from "@/features/progress/components/PercentChart";
import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useCourseStudent, useTeacherCourse } from "../hooks";

type DetailSectionProps = {
  id: string;
  title: string;
  description?: string;
  children: ReactNode;
};

function DetailSection({
  id,
  title,
  description,
  children,
}: DetailSectionProps) {
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

/** Style, its source, an open proposal and the trial, in the teacher's words. */
function ProfileSummary({
  profile,
  attention,
}: {
  profile: LearningProfile;
  attention: Attention | null;
}) {
  const lines = profileSummaryLines(profile);
  // R12, in words (no badge)
  if (attention) {
    lines.push({ label: "Wymaga uwagi", text: attentionSeries(attention) });
  }
  return (
    <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-[max-content_minmax(0,1fr)]">
      {lines.map((line) => (
        <div key={line.label} className="contents">
          <dt className="text-muted-foreground">{line.label}</dt>
          <dd>{line.text}</dd>
        </div>
      ))}
    </dl>
  );
}

type StudentDetailPageProps = { courseId: number; studentId: number };

/** What the student sees in "Moje postępy" for this course, plus the journal. */
export function StudentDetailPage({
  courseId,
  studentId,
}: StudentDetailPageProps) {
  const course = useTeacherCourse(courseId);
  const detail = useCourseStudent(courseId, studentId);
  const panelHref = `/teach/courses/${courseId}/panel`;

  if (course.isPending || detail.isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  const error = course.error ?? detail.error;
  if (error instanceof ApiError && error.status === 404) {
    return (
      <PageMessage
        icon={SearchXIcon}
        title="Nie znaleziono ucznia"
        description="Ten uczeń nie jest zapisany na kurs albo kurs został usunięty."
        action={
          <Link
            href={panelHref}
            className="text-sm font-medium underline underline-offset-4"
          >
            Wróć do panelu kursu
          </Link>
        }
      />
    );
  }
  if (error || !course.data || !detail.data) {
    return (
      <PageMessage
        icon={CloudOffIcon}
        title="Nie udało się wczytać danych ucznia"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={
          <Button
            onClick={() => {
              void course.refetch();
              void detail.refetch();
            }}
          >
            Spróbuj ponownie
          </Button>
        }
      />
    );
  }

  const { student, profile, history, lessons, journal, forms, attention } =
    detail.data;

  return (
    <div className="space-y-12">
      <div className="space-y-3">
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link href="/teach" className="hover:text-foreground">
            Moje kursy
          </Link>
          <span aria-hidden="true"> / </span>
          <Link
            href={`/teach/courses/${courseId}`}
            className="hover:text-foreground"
          >
            {course.data.title}
          </Link>
          <span aria-hidden="true"> / </span>
          <Link href={panelHref} className="hover:text-foreground">
            Panel kursu
          </Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{student.display_name}</span>
        </nav>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {student.display_name}
          </h1>
          <p className="text-muted-foreground">{student.email}</p>
        </div>
        <ProfileSummary profile={profile} attention={attention ?? null} />
      </div>

      <DetailSection
        id="student-forms"
        title="Procenty form"
        description="Profil ucznia ze wszystkich kursów: start z ankiety, potem +10 / −10 za pierwsze podejście w danej formie w lekcji."
      >
        <FormPercentages profile={profile} />
      </DetailSection>

      <DetailSection
        id="student-form-table"
        title="W której formie uczniowi idzie najlepiej"
        description="Jeden wiersz to jedna forma, liczby ze wszystkich kursów ucznia. „Za pierwszym razem” i „Średnia” liczą pierwsze podejście do lekcji w tej formie; procent zaliczeń pojawia się od 2 lekcji."
      >
        {forms ? (
          <FormTable forms={forms} style={profile.style} voice="neutral" />
        ) : (
          <p className="text-muted-foreground">Brak danych o formach.</p>
        )}
      </DetailSection>

      <DetailSection id="student-chart" title="Procenty w czasie">
        <PercentChart
          history={history}
          lessonNumbers={lessonNumbers(lessons)}
        />
      </DetailSection>

      <DetailSection id="student-lessons" title="Wyniki lekcji w tym kursie">
        <LessonResultsTable lessons={lessons} />
      </DetailSection>

      <DetailSection
        id="student-journal"
        title="Dziennik decyzji"
        description="Każda decyzja systemu w tym kursie z liczbami, z których wynika, oraz zmiany stylu i ankieta."
      >
        <DecisionJournal entries={journal} showCourse={false} />
      </DetailSection>
    </div>
  );
}
