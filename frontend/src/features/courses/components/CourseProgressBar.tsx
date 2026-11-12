type CourseProgressBarProps = { passed: number; total: number; label?: string };

/** "2 z 4 lekcji" with a thin bar. */
export function CourseProgressBar({
  passed,
  total,
  label,
}: CourseProgressBarProps) {
  const percent = total > 0 ? Math.round((passed / total) * 100) : 0;
  const text = `Zaliczone: ${passed} z ${total} lekcji`;
  return (
    <div className="space-y-1.5">
      <div
        role="progressbar"
        aria-label={label ?? "Postęp kursu"}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={passed}
        aria-valuetext={text}
        className="h-1.5 overflow-hidden rounded-full bg-muted"
      >
        <div
          className="h-full rounded-full bg-primary transition-[width]"
          style={{ width: `${percent}%` }}
        />
      </div>
      <p className="text-sm text-muted-foreground tabular-nums">{text}</p>
    </div>
  );
}
