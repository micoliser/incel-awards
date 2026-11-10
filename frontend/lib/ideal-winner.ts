/** Split stored ideal-winner text (one trait per line) into display lines. */
export function idealWinnerLines(text: string | null | undefined): string[] {
  if (!text) return [];
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}
