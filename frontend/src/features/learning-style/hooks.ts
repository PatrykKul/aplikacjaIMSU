import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { learningStyleApi } from "./api";
import type { LearningProfile, LearningStyle } from "./types";

const ROOT = "learning-style";

export const learningProfileKey = [ROOT, "profile"] as const;
const surveyQuestionsKey = [ROOT, "questions"] as const;
const surveyResultsKey = [ROOT, "results"] as const;
const personalizedBlocksKey = (lessonId: number) =>
  [ROOT, "lessons", lessonId] as const;

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

export function useSurveyResults() {
  return useQuery({
    queryKey: surveyResultsKey,
    queryFn: learningStyleApi.results,
  });
}

export function usePersonalizedBlocks(lessonId: number) {
  return useQuery({
    queryKey: personalizedBlocksKey(lessonId),
    queryFn: () => learningStyleApi.personalizedBlocks(lessonId),
  });
}

/** Records the first opening of a collapsed material (the server ignores repeats). */
export function useOpenMaterial(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (blockId: string) =>
      learningStyleApi.openMaterial(lessonId, blockId),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: personalizedBlocksKey(lessonId),
      }),
  });
}

/** After every change of the profile: store it and refetch lessons and history. */
function useProfileMutation<TArgs>(
  mutationFn: (args: TArgs) => Promise<LearningProfile>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: (profile) => {
      queryClient.setQueryData(learningProfileKey, profile);
      void queryClient.invalidateQueries({
        queryKey: [ROOT],
        predicate: (query) => query.queryKey[1] !== "profile",
      });
    },
  });
}

export function useSubmitSurvey() {
  return useProfileMutation(learningStyleApi.submitSurvey);
}

export function useChangeStyle() {
  return useProfileMutation((style: LearningStyle) =>
    learningStyleApi.changeStyle(style),
  );
}

export function useRestoreStyle() {
  return useProfileMutation(() => learningStyleApi.restoreStyle());
}

export function useAcceptProposal() {
  return useProfileMutation(() => learningStyleApi.acceptProposal());
}

export function useRejectProposal() {
  return useProfileMutation(() => learningStyleApi.rejectProposal());
}
