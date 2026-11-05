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
};

export function SkillCard({ courseId, skill, number }: SkillCardProps) {
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
        </div>
      </CardContent>
    </Card>
  );
}
