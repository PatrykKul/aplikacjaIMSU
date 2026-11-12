import type { Form } from "@/features/content/types";
import { api } from "@/shared/api/client";

import type {
  CourseHint,
  LearningProfile,
  Study,
  StudyState,
  SurveyChoice,
  SurveyQuestion,
} from "./types";

const PROFILE = "/profile/learning-style";

export const learningStyleApi = {
  questions: () => api.get<SurveyQuestion[]>("/survey/questions"),
  submitSurvey: (answers: SurveyChoice[]) =>
    api.post<LearningProfile>("/survey/answers", { answers }),

  profile: () => api.get<LearningProfile>(PROFILE),
  chooseTiedStyle: (style: Form) =>
    api.post<LearningProfile>(`${PROFILE}/tie-choice`, { style }),
  changeStyle: (style: Form) => api.put<LearningProfile>(PROFILE, { style }),
  acceptProposal: (id: number) =>
    api.post<LearningProfile>(`${PROFILE}/proposals/${id}/accept`),
  rejectProposal: (id: number) =>
    api.post<LearningProfile>(`${PROFILE}/proposals/${id}/reject`),

  study: (lessonId: number) => api.get<Study>(`/lessons/${lessonId}/study`),
  changeLessonForm: (
    lessonId: number,
    form: Form,
    source: "manual" | "suggestion",
  ) => api.put<Study>(`/lessons/${lessonId}/study/form`, { form, source }),

  studyStates: (courseId: number) =>
    api.get<StudyState[]>(`/courses/${courseId}/study-states`),
  courseHint: (courseId: number) =>
    api.get<CourseHint | null>(`/courses/${courseId}/hint`),
};
