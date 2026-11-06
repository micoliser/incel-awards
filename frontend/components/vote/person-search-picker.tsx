"use client";

import { useEffect, useId, useRef, useState, useTransition } from "react";
import { ApiRequestError, searchDirectory } from "@/lib/api";
import type { DirectoryPerson } from "@/lib/types";

type PersonSearchPickerProps = {
  year: number;
  token: string;
  awardName: string;
  value: { id: number; display_name: string } | null;
  onChange: (person: { id: number; display_name: string } | null) => void;
  disabled?: boolean;
};

export function PersonSearchPicker({
  year,
  token,
  awardName,
  value,
  onChange,
  disabled = false,
}: PersonSearchPickerProps) {
  const listId = useId();
  const inputId = useId();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<DirectoryPerson[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isPending, startTransition] = useTransition();
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const trimmed = query.trim();
  const canSearch = trimmed.length >= 2 && !disabled;
  const visibleResults = canSearch ? results : [];

  useEffect(() => {
    if (!canSearch) {
      queueMicrotask(() => {
        setResults([]);
        setActiveIndex(-1);
        setError(null);
      });
      return;
    }

    const handle = window.setTimeout(() => {
      startTransition(async () => {
        try {
          const people = await searchDirectory(year, token, trimmed);
          setResults(people);
          setError(null);
          setActiveIndex(people.length ? 0 : -1);
        } catch (err) {
          setResults([]);
          setActiveIndex(-1);
          setError(
            err instanceof ApiRequestError
              ? err.message
              : "Search failed. Try again.",
          );
        }
      });
    }, 280);

    return () => window.clearTimeout(handle);
  }, [canSearch, trimmed, year, token]);

  useEffect(() => {
    if (activeIndex < 0) return;
    optionRefs.current[activeIndex]?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  function selectPerson(person: DirectoryPerson) {
    onChange({
      id: person.id,
      display_name: person.display_name,
    });
    setQuery("");
    setResults([]);
    setActiveIndex(-1);
  }

  function onInputKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!canSearch || (!visibleResults.length && e.key !== "Escape")) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!visibleResults.length) return;
      setActiveIndex((i) => (i + 1) % visibleResults.length);
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!visibleResults.length) return;
      setActiveIndex(
        (i) => (i <= 0 ? visibleResults.length - 1 : i - 1),
      );
      return;
    }
    if (e.key === "Enter" && activeIndex >= 0 && visibleResults[activeIndex]) {
      e.preventDefault();
      selectPerson(visibleResults[activeIndex]);
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      setQuery("");
      setResults([]);
      setActiveIndex(-1);
    }
  }

  return (
    <div className="space-y-3">
      {value ? (
        <div className="flex flex-wrap items-center justify-between gap-3 border border-gold bg-[color-mix(in_srgb,var(--gold)_12%,var(--surface))] px-4 py-3">
          <div>
            <p className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted">
              Selected for {awardName}
            </p>
            <p className="mt-1 text-sm font-medium text-ink">{value.display_name}</p>
          </div>
          {!disabled ? (
            <button
              type="button"
              onClick={() => onChange(null)}
              className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-indigo underline-offset-4 hover:underline"
            >
              Clear
            </button>
          ) : null}
        </div>
      ) : null}

      <div>
        <label
          htmlFor={inputId}
          className="font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted"
        >
          Search colleagues
        </label>
        <p id={`${inputId}-hint`} className="mt-1 text-xs text-ink-muted">
          Eligible colleagues only. Type at least 2 letters; use arrows and
          Enter to pick.
        </p>
        <input
          id={inputId}
          type="search"
          autoComplete="off"
          disabled={disabled}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onInputKeyDown}
          placeholder="Name or department"
          className="mt-2 w-full border border-[var(--rule)] bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-ink-muted/70 disabled:cursor-not-allowed disabled:opacity-60"
          aria-controls={listId}
          aria-expanded={canSearch}
          aria-autocomplete="list"
          aria-activedescendant={
            activeIndex >= 0 && visibleResults[activeIndex]
              ? `${listId}-opt-${visibleResults[activeIndex].id}`
              : undefined
          }
          aria-describedby={`${inputId}-hint`}
          role="combobox"
        />
      </div>

      {error && canSearch ? (
        <p className="text-sm text-[var(--danger)]" role="alert">
          {error}
        </p>
      ) : null}

      {canSearch && !error ? (
        <ul
          id={listId}
          role="listbox"
          aria-label={`Search results for ${awardName}`}
          className="max-h-56 overflow-y-auto border border-[var(--rule)] bg-surface"
        >
          {isPending && !visibleResults.length ? (
            <li className="px-4 py-3 text-sm text-ink-muted">Searching…</li>
          ) : null}
          {!isPending && visibleResults.length === 0 ? (
            <li className="px-4 py-3 text-sm text-ink-muted">
              No colleagues match that search.
            </li>
          ) : null}
          {visibleResults.map((person, index) => {
            const selected = value?.id === person.id;
            const active = index === activeIndex;
            return (
              <li
                key={person.id}
                role="option"
                id={`${listId}-opt-${person.id}`}
                aria-selected={selected || active}
              >
                <button
                  type="button"
                  ref={(el) => {
                    optionRefs.current[index] = el;
                  }}
                  disabled={disabled}
                  onClick={() => selectPerson(person)}
                  className={`flex w-full flex-col items-start px-4 py-3 text-left transition-colors hover:bg-ground-deep focus-visible:bg-ground-deep focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-gold ${
                    selected || active
                      ? "bg-[color-mix(in_srgb,var(--gold)_12%,var(--surface))]"
                      : ""
                  }`}
                >
                  <span className="text-sm font-medium text-ink">
                    {person.display_name}
                  </span>
                  {person.department_name ? (
                    <span className="mt-0.5 text-xs text-ink-muted">
                      {person.department_name}
                    </span>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
