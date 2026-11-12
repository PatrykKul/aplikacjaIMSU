"use client";

import { QuizPoolPreview } from "@/features/assessment/components/QuizPoolPreview";
import { useCurrentUser } from "@/features/auth/hooks";
import { useLessonVersions } from "@/features/content/hooks";
import { FORMS } from "@/features/content/types";
import { FormMark } from "@/features/learning-style/components/FormMark";
import { formName } from "@/features/learning-style/explain";
import { ApiError } from "@/shared/api/client";
import { Spinner } from "@/shared/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";

import { useLesson } from "../hooks";
import { BlockList, LessonNav, LessonSection } from "./LessonParts";
import { LessonHeader } from "./LessonHeader";
import { LessonMessage } from "./LessonMessage";
import { PreviewBanner } from "./PreviewBanner";

type LessonPreviewProps = { courseId: number; lessonId: number };

/**
 * A lesson for its author and the admin: outline, the three versions V / A / K,
 * conclusions and the pool of questions with answers. Uses the editor's queries,
 * so the preview is fresh right after saving.
 */
export function LessonPreview({ courseId, lessonId }: LessonPreviewProps) {
  const { data: user } = useCurrentUser();
  const lesson = useLesson(lessonId);
  const versions = useLessonVersions(lessonId);

  if (lesson.isPending || versions.isPending) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner className="size-8" />
      </div>
    );
  }
  if (lesson.isError || versions.isError) {
    return (
      <LessonMessage
        error={lesson.error ?? versions.error}
        courseId={courseId}
        onRetry={() => {
          void lesson.refetch();
          void versions.refetch();
        }}
      />
    );
  }
  if (lesson.data.course.id !== courseId) {
    return (
      <LessonMessage
        error={new ApiError(404, "LESSON_NOT_FOUND")}
        courseId={courseId}
        onRetry={() => lesson.refetch()}
      />
    );
  }

  const data = lesson.data;
  const isAuthor = user?.id === data.course.owner_id;
  const courseHref = `/courses/${courseId}`;

  return (
    <>
      <LessonHeader
        courseHref={courseHref}
        courseTitle={data.course.title}
        title={`${data.number}. ${data.title}`}
      />
      <main className="mx-auto w-full max-w-3xl flex-1 space-y-10 px-4 py-8 sm:px-6">
        <div className="space-y-2">
          <PreviewBanner
            what="lekcję"
            editHref={
              isAuthor
                ? `/teach/courses/${courseId}/lessons/${lessonId}`
                : undefined
            }
          />
          {!data.is_published && (
            <p className="text-sm text-muted-foreground">
              Lekcja nie jest opublikowana – uczniowie jej nie widzą.
            </p>
          )}
        </div>

        <LessonSection id="lesson-outline" title="Zarys" doc={data.outline} />

        <section aria-labelledby="lesson-versions" className="space-y-4">
          <div className="space-y-1">
            <h2 id="lesson-versions" className="text-xl font-semibold">
              Wersje lekcji
            </h2>
            <p className="text-sm text-muted-foreground">
              Uczeń widzi jedną wersję – w formie swojego stylu albo tej, którą
              wybrał dla lekcji.
            </p>
          </div>
          <Tabs defaultValue="V">
            <TabsList className="w-full sm:w-fit">
              {FORMS.map((form) => (
                <TabsTrigger key={form} value={form}>
                  <FormMark form={form} />
                </TabsTrigger>
              ))}
            </TabsList>
            {FORMS.map((form) => (
              <TabsContent key={form} value={form} className="pt-4 text-base">
                <BlockList
                  blocks={versions.data[form]?.blocks ?? []}
                  label={`Wersja ${formName(form)}`}
                />
              </TabsContent>
            ))}
          </Tabs>
        </section>

        <LessonSection
          id="lesson-conclusions"
          title="Wnioski"
          doc={data.conclusions}
        />

        <QuizPoolPreview lessonId={lessonId} />

        <LessonNav lesson={data} courseHref={courseHref} />
      </main>
    </>
  );
}
