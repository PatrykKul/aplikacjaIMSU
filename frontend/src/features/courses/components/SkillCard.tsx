import Link from "next/link";

import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/shared/ui/card";
import { MathMarkdown } from "@/shared/ui/math-markdown";

import type { SkillSummary } from "../types";

type SkillCardProps = {
  courseId: number;
  skill: SkillSummary;
  number: number;
  // Required skills as shown to the student, e.g. "1. Skill A, 2. Skill B"
  requires: string[];
};

export function SkillCard({
  courseId,
  skill,
  number,
  requires,
}: SkillCardProps) {
  return (
    <Card className="relative transition-colors hover:bg-muted/50 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50">
      <CardContent className="flex gap-4">
        <span
          aria-hidden="true"
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-medium"
        >
          {number}
        </span>
        <div className="min-w-0 space-y-1">
          <CardTitle className="text-lg">
            <Link
              href={`/courses/${courseId}/skills/${skill.id}`}
              className="outline-none after:absolute after:inset-0"
            >
              {skill.title}
            </Link>
          </CardTitle>
          {skill.goal && (
            <CardDescription className="text-base">
              <MathMarkdown>{skill.goal}</MathMarkdown>
            </CardDescription>
          )}
          {requires.length > 0 && (
            <p className="text-sm text-muted-foreground">
              Wymaga: {requires.join(", ")}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
