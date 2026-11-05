import { Input } from "@/shared/ui/input";

type NumberAnswerProps = {
  id: string;
  unit: string | null;
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
  errorId?: string;
};

export function NumberAnswer({
  id,
  unit,
  value,
  onChange,
  disabled,
  errorId,
}: NumberAnswerProps) {
  return (
    <div className="flex items-center gap-2">
      <label htmlFor={id} className="sr-only">
        Twoja odpowiedź
      </label>
      <Input
        id={id}
        inputMode="decimal"
        autoComplete="off"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        aria-invalid={errorId ? "true" : undefined}
        aria-describedby={errorId}
        className="w-40 text-[17px] md:text-[17px]"
      />
      {unit && <span aria-hidden="true">{unit}</span>}
    </div>
  );
}
