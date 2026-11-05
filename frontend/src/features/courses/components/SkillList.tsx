import type { Course } from "../types";
import { SkillCard } from "./SkillCard";

export function SkillList({ course }: { course: Course }) {
  const skills = course.units.flatMap((unit) => unit.skills);
  const numberOf = new Map(skills.map((skill, index) => [skill.id, index + 1]));
  const labelOf = new Map(
    skills.map((skill) => [
      skill.id,
      `${numberOf.get(skill.id)}. ${skill.title}`,
    ]),
  );

  return (
    <div className="space-y-10">
      {course.units.map((unit) => (
        <section key={unit.id} aria-labelledby={`unit-${unit.id}`}>
          <h2 id={`unit-${unit.id}`} className="mb-4 text-xl font-semibold">
            {unit.title}
          </h2>
          <ol role="list" className="space-y-3">
            {unit.skills.map((skill) => (
              <li key={skill.id}>
                <SkillCard
                  courseId={course.id}
                  skill={skill}
                  number={numberOf.get(skill.id) ?? 0}
                  requires={skill.requires.flatMap(
                    (id) => labelOf.get(id) ?? [],
                  )}
                />
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}
