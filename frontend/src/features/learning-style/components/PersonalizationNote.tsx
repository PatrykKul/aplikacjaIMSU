"use client";

import { InfoIcon } from "lucide-react";
import Link from "next/link";

import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";

import { useLearningProfile } from "../hooks";
import { describeStyle } from "../styles";
import type { PersonalizedBlocks } from "../types";
import { StyleProposalBanner } from "./StyleProposalBanner";

function collapsedText(count: number): string {
  if (count === 1) {
    return "1 materiał dla innego stylu jest zwinięty – możesz go rozwinąć.";
  }
  const lastDigit = count % 10;
  const teen = count % 100 >= 12 && count % 100 <= 14;
  const few = lastDigit >= 2 && lastDigit <= 4 && !teen;
  return few
    ? `${count} materiały dla innych stylów są zwinięte – możesz je rozwinąć.`
    : `${count} materiałów dla innych stylów jest zwiniętych – możesz je rozwinąć.`;
}

/** "Why you see this" above a lesson, plus a style proposal if the system has one. */
export function PersonalizationNote({ data }: { data: PersonalizedBlocks }) {
  const isStudent = data.style !== null;
  const profile = useLearningProfile(isStudent);

  if (!isStudent) {
    return null; // teachers and admins see every block
  }

  return (
    <div className="space-y-3">
      <Alert>
        <InfoIcon />
        <AlertTitle>
          Lekcja dopasowana do stylu: {describeStyle(data.style!)}
        </AlertTitle>
        <AlertDescription>
          <p>
            <span className="font-medium text-foreground">
              Dlaczego to widzisz:{" "}
            </span>
            {data.explanation}
            {data.collapsed_block_ids.length > 0 && (
              <> {collapsedText(data.collapsed_block_ids.length)}</>
            )}{" "}
            <Link href="/profile">Zmień styl</Link>
          </p>
        </AlertDescription>
      </Alert>
      {profile.data?.proposal && (
        <StyleProposalBanner proposal={profile.data.proposal} />
      )}
    </div>
  );
}
