"use client";

import { CloudOffIcon, PencilIcon, SearchXIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import {
  EASY_ABOVE,
  HARD_BELOW,
  LESSON_MIN_STUDENTS,
  MATRIX_MIN_RESULTS,
  QUESTION_MIN_DRAWS,
} from "@/features/learning-style/explain";
import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useCourseStats, useEnrollments, useTeacherCourse } from "../hooks";
import { CourseStudentsTable } from "./CourseStudentsTable";
import { EnrollmentRequests } from "./EnrollmentRequests";
import { FormEffectiveness } from "./FormEffectiveness";
import { LessonDifficulty } from "./LessonDifficulty";
import { LessonFormMatrix } from "./LessonFormMatrix";
import { QuestionAnalysis } from "./QuestionAnalysis";
import { StyleDistribution } from "./StyleDistribution";

type PanelSectionProps = {
  id: string;
  title: string;
  description?: string;
  children: ReactNode;
};

function PanelSection({ id, title, description, children }: PanelSectionProps) {
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

/** "Panel kursu": enrollment requests, students and how the forms work. */
export function CoursePanel({ courseId }: { courseId: number }) {
  const course = useTeacherCourse(courseId);
  const enrollments = useEnrollments(courseId);
  const stats = useCourseStats(courseId);
  const queries = [course, enrollments, stats];

  if (queries.some((query) => query.isPending)) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  const error = queries.find((query) => query.error)?.error;
  if (error instanceof ApiError && error.status === 404) {
    return (
      <PageMessage
        icon={SearchXIcon}
        title="Nie znaleziono kursu"
        description="Kurs nie istnieje albo został usunięty."
        action={
          <Link
            href="/teach"
            className="text-sm font-medium underline underline-offset-4"
          >
            Wróć do moich kursów
          </Link>
        }
      />
    );
  }
  if (error || !course.data || !enrollments.data || !stats.data) {
    return (
      <PageMessage
        icon={CloudOffIcon}
        title="Nie udało się wczytać panelu kursu"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={
          <Button
            onClick={() => queries.forEach((query) => void query.refetch())}
          >
            Spróbuj ponownie
          </Button>
        }
      />
    );
  }

  const requests = enrollments.data.filter((e) => e.status === "pending");

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
          <span aria-current="page">Panel kursu</span>
        </nav>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="text-sm text-muted-foreground">{course.data.title}</p>
            <h1 className="text-2xl font-semibold tracking-tight">
              Panel kursu
            </h1>
          </div>
          <Link
            href={`/teach/courses/${courseId}`}
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            <PencilIcon data-icon="inline-start" />
            Edytuj kurs
          </Link>
        </div>
      </div>

      <PanelSection
        id="panel-requests"
        title={`Prośby o zapis (${requests.length})`}
        description="Uczeń widzi lekcje kursu dopiero po przyjęciu. Odrzucony może poprosić ponownie."
      >
        <EnrollmentRequests courseId={courseId} requests={requests} />
      </PanelSection>

      <PanelSection
        id="panel-students"
        title={`Uczniowie (${stats.data.students.length})`}
        description="Styl i procenty V / A / K ucznia, zaliczone lekcje tego kursu i średnia jego policzonych wyników. Kliknij ucznia, żeby zobaczyć wykres i dziennik decyzji. Uczeń, którego trzy ostatnie policzone wyniki są poniżej progu, ma przy imieniu dopisek „wymaga uwagi” z tymi wynikami."
      >
        <CourseStudentsTable
          courseId={courseId}
          students={stats.data.students}
        />
      </PanelSection>

      <PanelSection
        id="panel-lessons"
        title="Które lekcje sprawiają trudność"
        description={`Zaliczalność to odsetek uczniów, którzy zaliczyli lekcję, spośród tych, którzy ją rozpoczęli; procenty i średnie są podawane od ${LESSON_MIN_STUDENTS} uczniów w lekcji.`}
      >
        <LessonDifficulty
          lessons={stats.data.lessons}
          hardest={stats.data.hardest}
        />
      </PanelSection>

      <PanelSection
        id="panel-questions"
        title="Które pytania są za trudne albo źle ułożone"
        description={`Wylosowane to liczba wysłanych zestawów z tym pytaniem; procenty i ocena są podawane od ${QUESTION_MIN_DRAWS} wylosowań, a pytanie poniżej ${HARD_BELOW}% poprawnych odpowiedzi jest trudne, powyżej ${EASY_ABOVE}% łatwe.`}
      >
        <QuestionAnalysis courseId={courseId} />
      </PanelSection>

      <PanelSection
        id="panel-forms"
        title="Skuteczność form"
        description="Jak wypadają quizy przerobione w każdej z wersji lekcji tego kursu."
      >
        <FormEffectiveness forms={stats.data.forms} />
      </PanelSection>

      <PanelSection
        id="panel-matrix"
        title="W jakiej formie działa każda lekcja"
        description={`W komórce średnia pierwszych podejść w tej formie i liczba tych wyników; średnia pojawia się od ${MATRIX_MIN_RESULTS} wyników, wcześniej w komórce jest kreska.`}
      >
        <LessonFormMatrix
          matrix={stats.data.matrix}
          form_gaps={stats.data.form_gaps}
        />
      </PanelSection>

      <PanelSection
        id="panel-styles"
        title="Rozkład stylów"
        description="Aktywne style zapisanych uczniów."
      >
        <StyleDistribution styles={stats.data.styles} />
      </PanelSection>
    </div>
  );
}
