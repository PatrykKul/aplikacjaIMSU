import { api } from "@/shared/api/client";

import type {
  LearningProfile,
  LearningStyle,
  PersonalizedBlocks,
  SurveyChoice,
  SurveyQuestion,
  SurveyResult,
} from "./types";

const PROFILE = "/profile/learning-style";

export const learningStyleApi = {
  questions: () => api.get<SurveyQuestion[]>("/survey/questions"),
  submitSurvey: (answers: SurveyChoice[]) =>
    api.post<LearningProfile>("/survey/answers", { answers }),
  results: () => api.get<SurveyResult[]>("/survey/results"),

  profile: () => api.get<LearningProfile>(PROFILE),
  changeStyle: (style: LearningStyle) =>
    api.put<LearningProfile>(PROFILE, { style }),
  restoreStyle: () => api.delete<LearningProfile>(PROFILE),
  acceptProposal: () => api.post<LearningProfile>(`${PROFILE}/proposal/accept`),
  rejectProposal: () => api.post<LearningProfile>(`${PROFILE}/proposal/reject`),

  personalizedBlocks: (lessonId: number) =>
    api.get<PersonalizedBlocks>(`/lessons/${lessonId}/personalized-blocks`),
};
