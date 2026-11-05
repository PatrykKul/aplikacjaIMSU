export type CourseSummary = {
  id: number;
  key: string;
  title: string;
  description: string;
  is_published: boolean;
  is_archived: boolean;
};

export type SkillSummary = {
  id: number;
  key: string;
  title: string;
  goal: string;
  // Ids of the skills this skill requires
  requires: number[];
};

export type Unit = {
  id: number;
  key: string;
  title: string;
  skills: SkillSummary[];
};

export type Course = CourseSummary & { units: Unit[] };
