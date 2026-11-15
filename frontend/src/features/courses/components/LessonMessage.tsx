import {
  ClipboardListIcon,
  CloudOffIcon,
  LockIcon,
  SearchXIcon,
  UserPlusIcon,
} from "lucide-react";
import Link from "next/link";

import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";

import { isErrorCode, requiredLesson } from "../errors";

const linkClass = "text-sm font-medium underline underline-offset-4";

/** Full-screen state of a lesson that cannot be shown (lock, enrollment, 404, network). */
export function LessonMessage({
  error,
  courseId,
  onRetry,
}: {
  error: unknown;
  courseId: number;
  onRetry: () => void;
}) {
  const courseHref = `/courses/${courseId}`;
  const backToCourse = (
    <Link href={courseHref} className={linkClass}>
      Wróć do kursu
    </Link>
  );

  if (isErrorCode(error, "LESSON_LOCKED")) {
    const required = requiredLesson(error);
    return (
      <PageMessage
        fullScreen
        icon={LockIcon}
        title="Ta lekcja jest jeszcze zablokowana"
        description={
          required
            ? `Najpierw zalicz lekcję ${required.number}: „${required.title}” (quiz od 70%). Wtedy ta lekcja się otworzy.`
            : "Najpierw zalicz poprzednią lekcję (quiz od 70%)."
        }
        action={
          <div className="flex flex-col items-center gap-3">
            {required && (
              <Link
                href={`${courseHref}/lessons/${required.id}`}
                className={cn(buttonVariants())}
              >
                Przejdź do lekcji {required.number}
              </Link>
            )}
            {backToCourse}
          </div>
        }
      />
    );
  }
  if (isErrorCode(error, "ENROLLMENT_REQUIRED")) {
    return (
      <PageMessage
        fullScreen
        icon={UserPlusIcon}
        title="Najpierw zapisz się na kurs"
        description="Lekcje są dostępne po zapisaniu się na kurs i przyjęciu prośby przez nauczyciela."
        action={
          <Link href={courseHref} className={cn(buttonVariants())}>
            Przejdź do kursu i zapisz się
          </Link>
        }
      />
    );
  }
  if (isErrorCode(error, "SURVEY_REQUIRED")) {
    return (
      <PageMessage
        fullScreen
        icon={ClipboardListIcon}
        title="Najpierw wypełnij ankietę"
        description="Lekcje są dobierane do Twojego stylu uczenia się, a styl wynika z ankiety."
        action={
          <Link href="/survey" className={cn(buttonVariants())}>
            Przejdź do ankiety
          </Link>
        }
      />
    );
  }
  if (error instanceof ApiError && error.status === 404) {
    return (
      <PageMessage
        fullScreen
        icon={SearchXIcon}
        title="Nie znaleziono lekcji"
        description="Lekcja nie istnieje albo nie jest jeszcze dostępna."
        action={backToCourse}
      />
    );
  }
  return (
    <PageMessage
      fullScreen
      icon={CloudOffIcon}
      title="Nie udało się wczytać lekcji"
      description="Sprawdź połączenie i spróbuj ponownie."
      action={<Button onClick={onRetry}>Spróbuj ponownie</Button>}
    />
  );
}
