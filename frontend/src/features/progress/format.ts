const dateTime = new Intl.DateTimeFormat("pl-PL", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const shortDate = new Intl.DateTimeFormat("pl-PL", {
  day: "numeric",
  month: "short",
});

/** "12 lis 2026, 14:05" */
export function formatDateTime(iso: string): string {
  return dateTime.format(new Date(iso));
}

/** "12 lis" */
export function formatShortDate(iso: string): string {
  return shortDate.format(new Date(iso));
}
