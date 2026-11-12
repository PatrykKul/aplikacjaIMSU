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

import { formLabel, inFormLabel } from "../explain";
import { FORM_BAR } from "../form-tones";
import type { Study } from "../types";

type LessonFormBarProps = {
  study: Study;
  onChange: (form: Form) => void;
  pending?: boolean;
};

/** "Przerabiasz tę lekcję w formie: Słuchowej (A)" + a menu with the two other forms. */
export function LessonFormBar({
  study,
  onChange,
  pending,
}: LessonFormBarProps) {
  return (
    <div className="flex flex-col gap-3 border-y py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <span
          aria-hidden="true"
          className={cn(
            "mt-1.5 size-3 shrink-0 rounded-[3px]",
            FORM_BAR[study.form],
          )}
        />
        <div>
          <p>
            Przerabiasz tę lekcję w formie:{" "}
            <strong className="font-semibold">{inFormLabel(study.form)}</strong>
          </p>
          <p className="text-sm text-muted-foreground">
            {study.form_source === "choice"
              ? "Forma wybrana dla tej lekcji."
              : "Forma Twojego stylu uczenia się."}
          </p>
        </div>
      </div>
      {study.other_forms.length > 0 && (
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button
                variant="outline"
                disabled={pending}
                className="self-start sm:self-center"
              />
            }
          >
            {pending && <Spinner data-icon="inline-start" />}
            Przerób tę lekcję w innej formie
            <ChevronDownIcon data-icon="inline-end" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60">
            <DropdownMenuGroup>
              <DropdownMenuLabel>Wybierz formę</DropdownMenuLabel>
              {study.other_forms.map((form) => (
                <DropdownMenuItem key={form} onClick={() => onChange(form)}>
                  <span
                    aria-hidden="true"
                    className={cn("size-2.5 rounded-[2px]", FORM_BAR[form])}
                  />
                  {formLabel(form)}
                </DropdownMenuItem>
              ))}
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
}
