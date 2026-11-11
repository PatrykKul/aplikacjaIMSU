/** Polish noun form for a count: 1 kurs, 2 kursy, 5 kursów, 12 kursów, 22 kursy. */
export function plural(
  count: number,
  one: string,
  few: string,
  many: string,
): string {
  if (count === 1) {
    return one;
  }
  const lastDigit = count % 10;
  const lastTwoDigits = count % 100;
  const isFew =
    lastDigit >= 2 &&
    lastDigit <= 4 &&
    (lastTwoDigits < 12 || lastTwoDigits > 14);
  return isFew ? few : many;
}
