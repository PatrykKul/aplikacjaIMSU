import type { ReactNode, Ref } from "react";

import { cn } from "@/shared/lib/utils";
import { Card, CardContent } from "@/shared/ui/card";

type StepCardProps = {
  active?: boolean;
  label?: string;
  ref?: Ref<HTMLDivElement>;
  children: ReactNode;
};

// One step of the lesson. tabIndex={-1} lets the player move focus here
// when the step appears, without adding it to the Tab order.
export function StepCard({ active, label, ref, children }: StepCardProps) {
  return (
    <Card
      ref={ref}
      tabIndex={-1}
      className={cn(
        "scroll-mt-24 gap-0 py-5 text-[17px] leading-[1.65] outline-none [--card-spacing:--spacing(5)] sm:py-8 sm:[--card-spacing:--spacing(9)]",
        active && "ring-2 ring-foreground/40",
      )}
    >
      <CardContent className="max-w-[65ch] space-y-4">
        {label && <p className="text-sm text-muted-foreground">{label}</p>}
        {children}
      </CardContent>
    </Card>
  );
}
