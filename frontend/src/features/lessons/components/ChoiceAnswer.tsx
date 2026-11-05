import { MathMarkdown } from "@/shared/ui/math-markdown";

type ChoiceAnswerProps = {
  name: string;
  options: string[];
  value: number | null;
  onChange: (value: number) => void;
  disabled: boolean;
  errorId?: string;
};

// Native radio buttons: arrow keys, Space and screen readers work as usual
export function ChoiceAnswer({
  name,
  options,
  value,
  onChange,
  disabled,
  errorId,
}: ChoiceAnswerProps) {
  return (
    <fieldset aria-describedby={errorId} className="space-y-2">
      <legend className="sr-only">Twoja odpowiedź</legend>
      {options.map((option, index) => (
        <label
          key={index}
          className="flex min-h-control cursor-pointer items-center gap-3 rounded-lg px-4 py-2 ring-1 ring-foreground/15 transition-colors hover:bg-muted/50 has-checked:ring-2 has-checked:ring-foreground has-focus-visible:ring-3 has-focus-visible:ring-ring/50 has-disabled:cursor-default has-disabled:hover:bg-transparent"
        >
          <input
            type="radio"
            name={name}
            value={index}
            checked={value === index}
            onChange={() => onChange(index)}
            disabled={disabled}
            className="size-4 shrink-0 accent-foreground"
          />
          <MathMarkdown inline>{option}</MathMarkdown>
        </label>
      ))}
    </fieldset>
  );
}
