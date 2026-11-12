import {
  type QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import type { Form } from "@/features/content/types";

import { learningStyleApi } from "./api";
import type { LearningProfile, Study } from "./types";

export const learningProfileKey = ["learning-style", "profile"] as const;
const surveyQuestionsKey = ["learning-style", "questions"] as const;
export const studyKey = (lessonId: number) =>
  ["lessons", lessonId, "study"] as const;
export const lessonQuizKey = (lessonId: number) =>
  ["lessons", lessonId, "quiz"] as const;
export const courseHintKey = (courseId: number) =>
  ["courses", courseId, "hint"] as const;

export function useLearningProfile(enabled = true) {
  return useQuery({
    queryKey: learningProfileKey,
    queryFn: learningStyleApi.profile,
    enabled,
  });
}

export function useSurveyQuestions() {
  return useQuery({
    queryKey: surveyQuestionsKey,
    queryFn: learningStyleApi.questions,
    staleTime: Infinity,
  });
}

/** Every lesson studied so far shows the version of the (new) style. */
function refreshAfterStyleChange(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({
      predicate: (query) =>
        query.queryKey[0] === "lessons" && query.queryKey[2] === "study",
    }),
    queryClient.invalidateQueries({ queryKey: ["me"] }),
  ]);
}

/** After every change of the profile: store it and refetch what depends on the style. */
function useProfileMutation<TArgs>(
  mutationFn: (args: TArgs) => Promise<LearningProfile>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: (profile) => {
      queryClient.setQueryData(learningProfileKey, profile);
      return refreshAfterStyleChange(queryClient);
    },
  });
}

export function useSubmitSurvey() {
  return useProfileMutation(learningStyleApi.submitSurvey);
}

export function useChooseTiedStyle() {
  return useProfileMutation(learningStyleApi.chooseTiedStyle);
}

export function useChangeStyle() {
  return useProfileMutation(learningStyleApi.changeStyle);
}

export function useAcceptProposal() {
  return useProfileMutation(learningStyleApi.acceptProposal);
}

export function useRejectProposal() {
  return useProfileMutation(learningStyleApi.rejectProposal);
}

/** The lesson in the form of the student (version, suggestion, last result). */
export function useStudy(lessonId: number, enabled = true) {
  return useQuery({
    queryKey: studyKey(lessonId),
    queryFn: () => learningStyleApi.study(lessonId),
    enabled,
  });
}

/** "Przerób tę lekcję w innej formie": new version and a new set of questions. */
export function useChangeLessonForm(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      form,
      source,
    }: {
      form: Form;
      source: "manual" | "suggestion";
    }) => learningStyleApi.changeLessonForm(lessonId, form, source),
    onSuccess: (study: Study) => {
      queryClient.setQueryData(studyKey(lessonId), study);
      return Promise.all([
        queryClient.invalidateQueries({ queryKey: lessonQuizKey(lessonId) }),
        queryClient.invalidateQueries({ queryKey: ["me", "journal"] }),
      ]);
    },
  });
}

/** R8; null when other students have no results yet. */
export function useCourseHint(courseId: number, enabled: boolean) {
  return useQuery({
    queryKey: courseHintKey(courseId),
    queryFn: () => learningStyleApi.courseHint(courseId),
    enabled,
  });
}
