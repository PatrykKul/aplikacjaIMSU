"use client";

import { ChevronDownIcon } from "lucide-react";

import type { Form } from "@/features/content/types";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import { Spinner } from "@/shared/ui/spinner";

import { formLabel, lessonFormText } from "../explain";
import { FORM_BAR } from "../form-tones";
import type { Study } from "../types";

type LessonFormBarProps = {
  study: Study;
  onChange: (form: Form) => void;
  pending?: boolean;
};

/**
 * D57: one calm line "Forma: Wzrokowa (Twój styl) · Zmień formę tej lekcji";
 * the change is a menu with the two other forms, not a big button.
 */
export function LessonFormBar({
  study,
  onChange,
  pending,
}: LessonFormBarProps) {
  // Only an explicit choice of another form than the style counts as a choice
  const chosen = study.form_source === "choice" && study.form !== study.style;
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
      <span
        aria-hidden="true"
        className={cn("size-2.5 shrink-0 rounded-[2px]", FORM_BAR[study.form])}
      />
      <p>
        Forma:{" "}
        <span className="font-medium text-foreground">
          {lessonFormText(study.form, chosen)}
        </span>
      </p>
      {study.other_forms.length > 0 && (
        <>
          {/* On a phone the link wraps to its own line, without a lone dot */}
          <span aria-hidden="true" className="hidden sm:inline">
            ·
          </span>
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button
                  variant="link"
                  size="sm"
                  disabled={pending}
                  className="h-9 px-0 text-sm text-foreground underline underline-offset-4 hover:text-primary"
                />
              }
            >
              {pending && <Spinner data-icon="inline-start" />}
              {chosen ? "Zmień formę" : "Zmień formę tej lekcji"}
              <ChevronDownIcon data-icon="inline-end" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-60">
              <DropdownMenuGroup>
                <DropdownMenuLabel>
                  Przerób tę lekcję w formie
                </DropdownMenuLabel>
                {study.other_forms.map((form) => (
                  <DropdownMenuItem key={form} onClick={() => onChange(form)}>
                    <span
                      aria-hidden="true"
                      className={cn("size-2.5 rounded-[2px]", FORM_BAR[form])}
                    />
                    {formLabel(form)}
                    {form === study.style && (
                      <span className="ml-auto text-xs text-muted-foreground">
                        Twój styl
                      </span>
                    )}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </>
      )}
    </div>
  );
}
