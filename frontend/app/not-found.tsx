import Link from "next/link";
import { SiteHeader } from "@/components/site-header";

export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto flex max-w-xl flex-1 flex-col justify-center px-5 py-24 sm:px-8">
        <h1 className="font-[family-name:var(--font-display)] text-3xl tracking-tight text-ink">
          Page not found
        </h1>
        <p className="mt-4 text-ink-muted">
          That year or award is not available. Return to the overview to pick a
          published season.
        </p>
        <Link
          href="/"
          className="mt-8 inline-flex w-fit bg-gradient-to-r from-gold to-gold-bright px-5 py-3 font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-ground hover:brightness-110"
        >
          Incel Group Awards home
        </Link>
      </main>
    </>
  );
}
