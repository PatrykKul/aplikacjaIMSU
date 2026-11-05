from pydantic import BaseModel, ConfigDict


class CourseSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    description: str
    is_published: bool
    is_archived: bool


class SkillSummaryResponse(BaseModel):
    id: int
    key: str
    title: str
    goal: str
    # Ids of the skills this skill requires (prerequisite graph)
    requires: list[int]


class UnitResponse(BaseModel):
    id: int
    key: str
    title: str
    skills: list[SkillSummaryResponse]


class CourseResponse(CourseSummaryResponse):
    units: list[UnitResponse]


class SkillResponse(SkillSummaryResponse):
    course_id: int
    unit_id: int


class CourseUpdateRequest(BaseModel):
    is_published: bool
