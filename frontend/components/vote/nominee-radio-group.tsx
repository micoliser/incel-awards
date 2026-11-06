"use client";

import type { Nominee } from "@/lib/types";

type NomineeRadioGroupProps = {
  awardSlug: string;
  awardName: string;
  nominees: Nominee[];
  value: number | null;
  onChange: (nomineeId: number) => void;
  disabled?: boolean;
};

export function NomineeRadioGroup({
  awardSlug,
  awardName,
  nominees,
  value,
  onChange,
  disabled = false,
}: NomineeRadioGroupProps) {
  const groupName = `award-${awardSlug}`;

  return (
    <fieldset disabled={disabled} className="min-w-0">
      <legend className="sr-only">Choose a nominee for {awardName}</legend>
      <ul className="space-y-2">
        {nominees.map((nominee) => {
          const inputId = `${groupName}-${nominee.id}`;
          const selected = value === nominee.id;
          return (
            <li key={nominee.id}>
              <label
                htmlFor={inputId}
                className={`flex cursor-pointer items-start gap-3 border px-4 py-3 transition-colors duration-200 ${
                  selected
                    ? "border-gold bg-[color-mix(in_srgb,var(--gold)_12%,var(--surface))]"
                    : "border-[var(--rule)] bg-surface hover:border-gold/40"
                } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
              >
                <input
                  id={inputId}
                  type="radio"
                  name={groupName}
                  value={nominee.id}
                  checked={selected}
                  onChange={() => onChange(nominee.id)}
                  className="mt-1 h-4 w-4 shrink-0 accent-indigo"
                />
                <span className="min-w-0 text-sm font-medium text-ink">
                  {nominee.display_name}
                </span>
              </label>
            </li>
          );
        })}
      </ul>
    </fieldset>
  );
}
