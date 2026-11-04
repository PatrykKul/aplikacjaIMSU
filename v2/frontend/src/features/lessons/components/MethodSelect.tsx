"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";

import { methodLabels } from "../methods";
import type { LessonMethod } from "../types";

type MethodSelectProps = {
  methods: LessonMethod[];
  value: LessonMethod;
  onChange: (method: LessonMethod) => void;
};

// Teachers and admins preview each variant of the lesson
export function MethodSelect({ methods, value, onChange }: MethodSelectProps) {
  const items = methods.map((method) => ({
    value: method,
    label: methodLabels[method],
  }));

  return (
    <Select
      items={items}
      value={value}
      onValueChange={(next) => {
        if (next && next !== value) {
          onChange(next as LessonMethod);
        }
      }}
    >
      <SelectTrigger
        aria-label="Wariant lekcji"
        className="w-24 shrink-0 sm:w-32"
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {items.map((item) => (
          <SelectItem key={item.value} value={item.value}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
