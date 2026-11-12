"use client";

import { SparklesIcon } from "lucide-react";
import { useState } from "react";

import { Button } from "@/shared/ui/button";

import { learningStyleError } from "../errors";
import {
  proposalEffect,
  proposalEvidenceText,
  proposalTitle,
  styleName,
} from "../explain";
import { useAcceptProposal, useRejectProposal } from "../hooks";
import type { Proposal } from "../types";

/** R6 / R7: a proposal to change the style, with the numbers; the student decides. */
export function StyleProposalBanner({ proposal }: { proposal: Proposal }) {
  const accept = useAcceptProposal();
  const reject = useRejectProposal();
  const [decision, setDecision] = useState<"accepted" | "rejected" | null>(
    null,
  );
  const busy = accept.isPending || reject.isPending;
  const error = accept.error ?? reject.error;
  const evidence = proposalEvidenceText(proposal.evidence);

  if (decision) {
    return (
      <div role="status" className="border-l-2 border-primary py-1 pl-4">
        {decision === "accepted"
          ? `Styl zmieniony na ${styleName(proposal.to)}. Zmiana trafiła do dziennika.`
          : "Zostajesz przy swoim stylu. Propozycja wróci najwcześniej po 2 nowych wynikach."}
      </div>
    );
  }

  return (
    <section
      aria-label="Propozycja zmiany stylu"
      className="space-y-3 rounded-lg border border-primary/40 bg-accent/40 p-4 sm:p-5"
    >
      <div className="flex gap-3">
        <SparklesIcon
          aria-hidden="true"
          className="mt-0.5 size-5 shrink-0 text-primary"
        />
        <div className="space-y-1.5">
          <p className="font-medium">{proposalTitle(proposal)}</p>
          {evidence && (
            <p className="tabular-nums">
              <span className="text-muted-foreground">Dlaczego: </span>
              {evidence}
            </p>
          )}
          <p className="text-sm text-muted-foreground">
            {proposalEffect(proposal)}
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 sm:pl-8">
        <Button
          disabled={busy}
          onClick={() =>
            accept.mutate(proposal.id, {
              onSuccess: () => setDecision("accepted"),
            })
          }
        >
          Przełącz na stałe
        </Button>
        <Button
          variant="outline"
          disabled={busy}
          onClick={() =>
            reject.mutate(proposal.id, {
              onSuccess: () => setDecision("rejected"),
            })
          }
        >
          Zostaję przy swoim
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-sm text-destructive sm:pl-8">
          {learningStyleError(error)}
        </p>
      )}
    </section>
  );
}
