"use client";

import { InfoIcon } from "lucide-react";
import Link from "next/link";

import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";

import { useLearningProfile } from "../hooks";
import { describeStyle } from "../styles";
import type { PersonalizedBlocks } from "../types";
import { StyleProposalBanner } from "./StyleProposalBanner";

function hiddenText(count: number): string {
  if (count === 1) return "Ukryto 1 materiał przeznaczony dla innego stylu.";
  const lastDigit = count % 10;
  const teen = count % 100 >= 12 && count % 100 <= 14;
  const few = lastDigit >= 2 && lastDigit <= 4 && !teen;
  return `Ukryto ${count} ${few ? "materiały przeznaczone" : "materiałów przeznaczonych"} dla innych stylów.`;
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
        <AlertTitle>Lekcja dopasowana do stylu: {describeStyle(data.style!)}</AlertTitle>
        <AlertDescription>
          <p>
            <span className="font-medium text-foreground">Dlaczego to widzisz: </span>
            {data.explanation}
            {data.hidden_count > 0 && <> {hiddenText(data.hidden_count)}</>}{" "}
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
