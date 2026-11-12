"use client";

import { CloudOffIcon, EyeIcon, PencilIcon, SearchXIcon } from "lucide-react";
import Link from "next/link";
import { type MouseEvent, useCallback, useState } from "react";

import { FORMS } from "@/features/content/types";
import { ApiError } from "@/shared/api/client";
import {
  confirmLeave,
  useUnsavedChangesWarning,
} from "@/shared/hooks/use-unsaved-changes-warning";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";

import {
  EDITOR_TABS,
  type EditorTab,
  TAB_LABELS,
  tabOfArea,
} from "../editor-tabs";
import { useLessonVersions, useQuestionPool, useTeacherLesson } from "../hooks";
import type { LessonVersions, QuizPool, TeacherLesson } from "../types";
import { OutlineEditor } from "./OutlineEditor";
import { PoolEditor } from "./PoolEditor";
import { ReadinessPanel } from "./ReadinessPanel";
import { RenameLessonDialog } from "./RenameLessonDialog";
import { VersionEditor } from "./VersionEditor";

type LessonEditorProps = {
  courseId: number;
  lessonId: number;
  initialTab?: EditorTab;
};

export function LessonEditor({
  courseId,
  lessonId,
  initialTab = "outline",
}: LessonEditorProps) {
  const lesson = useTeacherLesson(lessonId);
  const versions = useLessonVersions(lessonId);
  const pool = useQuestionPool(lessonId);
  const queries = [lesson, versions, pool];

  if (queries.some((query) => query.isPending)) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  const error = queries.find((query) => query.error)?.error;
  // A lesson of another course in the address is "not found" as well
  if (
    (error instanceof ApiError && error.status === 404) ||
    (lesson.data && lesson.data.course.id !== courseId)
  ) {
    return (
      <PageMessage
        icon={SearchXIcon}
        title="Nie znaleziono lekcji"
        description="Lekcja nie istnieje albo została usunięta."
        action={
          <Link
            href={`/teach/courses/${courseId}`}
            className="text-sm font-medium underline underline-offset-4"
          >
            Wróć do kursu
          </Link>
        }
      />
    );
  }
  if (error || !lesson.data || !versions.data || !pool.data) {
    return (
      <PageMessage
        icon={CloudOffIcon}
        title="Nie udało się wczytać lekcji"
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

  return (
    <LessonWorkspace
      lesson={lesson.data}
      versions={versions.data}
      pool={pool.data}
      initialTab={initialTab}
    />
  );
}

type LessonWorkspaceProps = {
  lesson: TeacherLesson;
  versions: LessonVersions;
  pool: QuizPool;
  initialTab: EditorTab;
};

function LessonWorkspace({
  lesson,
  versions,
  pool,
  initialTab,
}: LessonWorkspaceProps) {
  const [tab, setTab] = useState<EditorTab>(initialTab);
  const [dirtyTabs, setDirtyTabs] = useState<Record<EditorTab, boolean>>({
    outline: false,
    V: false,
    A: false,
    K: false,
    quiz: false,
  });
  const [renaming, setRenaming] = useState(false);
  const dirty = Object.values(dirtyTabs).some(Boolean);
  useUnsavedChangesWarning(dirty);

  const courseHref = `/teach/courses/${lesson.course.id}`;

  // One stable callback per tab, so the editors' effects do not loop
  const [dirtyHandlers] = useState(
    () =>
      Object.fromEntries(
        EDITOR_TABS.map((key) => [
          key,
          (value: boolean) =>
            setDirtyTabs((current) =>
              current[key] === value ? current : { ...current, [key]: value },
            ),
        ]),
      ) as Record<EditorTab, (dirty: boolean) => void>,
  );

  const showTab = useCallback((next: EditorTab) => {
    setTab(next);
    // Keep the tab in the address, so a reload opens the same one
    window.history.replaceState(null, "", `?tab=${next}`);
  }, []);

  function leaveUnlessDirty(event: MouseEvent) {
    if (!confirmLeave(dirty)) {
      event.preventDefault();
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link
            href="/teach"
            className="hover:text-foreground"
            onClick={leaveUnlessDirty}
          >
            Moje kursy
          </Link>
          <span aria-hidden="true"> / </span>
          <Link
            href={courseHref}
            className="hover:text-foreground"
            onClick={leaveUnlessDirty}
          >
            {lesson.course.title}
          </Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{lesson.title}</span>
        </nav>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="min-w-0">
            <p className="text-sm text-muted-foreground">
              Lekcja {lesson.number}
            </p>
            <h1 className="text-2xl font-semibold tracking-tight">
              {lesson.title}
            </h1>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => setRenaming(true)}>
              <PencilIcon data-icon="inline-start" />
              Zmień nazwę
            </Button>
            {/* The preview shows the saved lesson, so unsaved changes need a confirmation */}
            <Link
              href={`/courses/${lesson.course.id}/lessons/${lesson.id}`}
              className={cn(buttonVariants({ variant: "outline" }))}
              onClick={leaveUnlessDirty}
            >
              <EyeIcon data-icon="inline-start" />
              Podgląd
            </Link>
          </div>
        </div>
      </div>

      <ReadinessPanel
        lesson={lesson}
        dirty={dirty}
        onShowArea={(area) => showTab(tabOfArea(area))}
      />

      <Tabs
        value={tab}
        onValueChange={(value) => showTab(value as EditorTab)}
        className="gap-4"
      >
        {/* Five tabs do not fit a phone: the list scrolls sideways */}
        <div className="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
          <TabsList className="w-max">
            {EDITOR_TABS.map((key) => (
              <TabsTrigger key={key} value={key}>
                {TAB_LABELS[key]}
                {dirtyTabs[key] && (
                  <>
                    <span
                      aria-hidden="true"
                      className="size-1.5 rounded-full bg-primary"
                    />
                    <span className="sr-only">(niezapisane zmiany)</span>
                  </>
                )}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {/* Kept mounted: switching tabs must not drop unsaved edits */}
        <TabsContent value="outline" keepMounted className="text-base">
          <OutlineEditor
            lesson={lesson}
            onDirtyChange={dirtyHandlers.outline}
          />
        </TabsContent>
        {FORMS.map((form) => (
          <TabsContent
            key={form}
            value={form}
            keepMounted
            className="text-base"
          >
            <VersionEditor
              lessonId={lesson.id}
              form={form}
              initialBlocks={versions[form]?.blocks ?? []}
              onDirtyChange={dirtyHandlers[form]}
            />
          </TabsContent>
        ))}
        <TabsContent value="quiz" keepMounted className="text-base">
          <PoolEditor
            lessonId={lesson.id}
            initial={pool.questions}
            onDirtyChange={dirtyHandlers.quiz}
          />
        </TabsContent>
      </Tabs>

      <RenameLessonDialog
        lesson={renaming ? lesson : null}
        onClose={() => setRenaming(false)}
      />
    </div>
  );
}
