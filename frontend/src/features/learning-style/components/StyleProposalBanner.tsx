"use client";

import { SparklesIcon } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";

import { learningStyleError } from "../errors";
import { useAcceptProposal, useRejectProposal } from "../hooks";
import type { StyleProposal } from "../types";

/** "Lepiej Ci idzie z materiałami słuchowymi – przełączyć?" with the reason; the student decides. */
export function StyleProposalBanner({ proposal }: { proposal: StyleProposal }) {
  const accept = useAcceptProposal();
  const reject = useRejectProposal();
  const busy = accept.isPending || reject.isPending;
  const error = accept.error ?? reject.error;

  return (
    <Alert className="border-primary/40 bg-primary/5">
      <SparklesIcon />
      <AlertTitle>{proposal.message}</AlertTitle>
      <AlertDescription className="space-y-3">
        <p>
          <span className="font-medium text-foreground">Dlaczego to widzisz: </span>
          {proposal.why}
        </p>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" disabled={busy} onClick={() => accept.mutate(undefined)}>
            Przełącz
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => reject.mutate(undefined)}
          >
            Zostaję przy swoim
          </Button>
        </div>
        {error && <p className="text-destructive">{learningStyleError(error)}</p>}
      </AlertDescription>
    </Alert>
  );
}
