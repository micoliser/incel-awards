import { idealWinnerLines } from "@/lib/ideal-winner";

export function IdealWinnerList({
  text,
  className = "",
}: {
  text: string | null | undefined;
  className?: string;
}) {
  const lines = idealWinnerLines(text);
  if (!lines.length) return null;

  return (
    <ul className={`list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-ink ${className}`}>
      {lines.map((line) => (
        <li key={line}>{line}</li>
      ))}
    </ul>
  );
}
