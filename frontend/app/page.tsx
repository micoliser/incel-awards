import Image from "next/image";
import Link from "next/link";
import { ConfettiSplash } from "@/components/confetti-splash";
import { SiteHeader } from "@/components/site-header";
import { YearStatusBadge } from "@/components/year-status-badge";
import {
  IconBallot,
  IconBuilding,
  IconMail,
  IconStar,
  IconUsers,
} from "@/components/icons";
import { getCurrentYear, listYears } from "@/lib/api";
import { yearStatusLabel } from "@/lib/format";

/** Home fetches live year data from the API; allow blocking navigation. */
export const instant = false;

export default async function HomePage() {
  const current = await getCurrentYear();
  const years = await listYears();
  const archive = years
    .filter((y) => !current || y.year !== current.year)
    .sort((a, b) => b.year - a.year);

  return (
    <>
      <ConfettiSplash />
      <SiteHeader
        year={current?.year}
        votingOpensAt={current?.voting_opens_at}
        votingClosesAt={current?.voting_closes_at}
        overlay
      />
      <main className="flex-1">
        <section className="relative min-h-[min(100svh,900px)] overflow-hidden">
          <Image
            src="/images/hero-afro-classy-eoyp26.jpg"
            alt=""
            fill
            priority
            className="object-cover object-[center_40%]"
            sizes="100vw"
          />
          <div
            className="absolute inset-0 bg-gradient-to-t from-[color-mix(in_srgb,var(--ground)_96%,transparent)] via-[color-mix(in_srgb,var(--ground)_72%,transparent)] to-[color-mix(in_srgb,var(--ground)_45%,transparent)]"
            aria-hidden
          />
          <div className="relative mx-auto flex min-h-[min(100svh,900px)] max-w-6xl flex-col justify-end px-5 pb-16 pt-28 sm:px-8 sm:pb-24 sm:pt-36">
            <p className="animate-weft font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.28em] text-gold">
              Annual recognition
            </p>
            <p className="animate-weft animate-weft-delay-1 mt-4 font-[family-name:var(--font-display)] text-4xl font-semibold tracking-tight text-ink sm:text-6xl md:text-[4.75rem]">
              <span className="gold-shimmer">Incel Group</span>
            </p>
            <h1 className="animate-weft animate-weft-delay-2 mt-4 max-w-2xl font-[family-name:var(--font-display)] text-2xl font-semibold leading-tight tracking-tight text-ink sm:text-4xl">
              Employee Awards
            </h1>
            <p className="animate-weft animate-weft-delay-3 mt-4 max-w-xl text-base leading-relaxed text-ink-muted sm:text-lg">
              A yearly season of recognition for people and teams who raise the
              standard across Tourism, Global, and the whole company.
            </p>
            <div className="animate-weft animate-weft-delay-3 mt-8 flex flex-wrap items-center gap-5">
              {current ? (
                <>
                  <Link
                    href={`/${current.year}`}
                    className="inline-flex items-center bg-gradient-to-r from-gold to-gold-bright px-7 py-3.5 font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.16em] text-ground transition-[filter,transform] duration-300 hover:brightness-110 hover:scale-[1.02]"
                  >
                    Enter {current.year} season
                  </Link>
                  <YearStatusBadge status={current.status} />
                </>
              ) : (
                <p className="text-sm text-ink-muted">
                  The next awards season will appear here when it is published.
                </p>
              )}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="axial-rule mb-10" />
          <div className="grid gap-12 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:gap-16">
            <div>
              <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-ink sm:text-3xl">
                What we celebrate
              </h2>
              <p className="mt-5 max-w-prose text-base leading-relaxed text-ink-muted sm:text-lg">
                Across Incel Group, people make the difference every day. In
                Tourism, that may be the calm that steadies a guest journey or
                the care that turns a booking into a lasting memory. In Global,
                it may be the quiet accuracy behind a transfer, a control, or a
                system that keeps the business moving.
              </p>
              <p className="mt-4 max-w-prose text-base leading-relaxed text-ink-muted">
                We set aside this season to honour colleagues who raise the bar
                for others: those who show up with integrity, who lift their
                teams, who invent better ways of working, and who make our
                workplaces kinder and sharper at the same time.
              </p>
              <p className="mt-4 max-w-prose text-base leading-relaxed text-ink-muted">
                Recognition is not only for the loudest wins. It is also for
                steady reliability, generous collaboration, and the kind of
                leadership that does not always need a title.
              </p>
            </div>

            <div className="space-y-8 border-t border-[var(--rule)] pt-8 lg:border-l lg:border-t-0 lg:pl-12 lg:pt-0">
              <div>
                <span className="mb-3 block h-1 w-10 bg-tourism" aria-hidden />
                <h3 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
                  Hospitality in motion
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                  People who protect the guest experience, keep promises under
                  pressure, and carry Incel Tourism with pride from first
                  enquiry to final farewell.
                </p>
              </div>
              <div>
                <span className="mb-3 block h-1 w-10 bg-global" aria-hidden />
                <h3 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
                  Precision that scales
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                  People who strengthen Global operations with clarity,
                  controls, and ideas that make the whole organisation more
                  capable.
                </p>
              </div>
              <div>
                <span className="mb-3 block h-1 w-10 bg-shared" aria-hidden />
                <h3 className="font-[family-name:var(--font-display)] text-xl tracking-tight text-ink">
                  Character we share
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                  People who make Incel Group a better place to work: mentors,
                  teammates, and culture-keepers whose example travels across
                  desks and departments.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-[var(--rule)] bg-[color-mix(in_srgb,var(--ground-deep)_45%,var(--ground))]">
          <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 py-16 sm:px-8 lg:grid-cols-2 lg:gap-16">
            <div className="relative aspect-[4/3] overflow-hidden bg-surface">
              <Image
                src="/images/season-ceremony.jpg"
                alt="Colleagues celebrating recognition at Incel Group Employee Awards"
                fill
                className="object-cover object-[center_20%]"
                sizes="(max-width: 1024px) 100vw, 50vw"
                priority={false}
              />
            </div>
            <div>
              <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-ink sm:text-3xl">
                How a season works
              </h2>
              <p className="mt-3 max-w-prose text-sm leading-relaxed text-ink-muted">
                A simple rhythm each year: notice the people who stood out,
                invite every colleague to take part, then listen to the room.
              </p>
              <ol className="mt-8 space-y-8">
                <li className="grid grid-cols-[auto_1fr] gap-4">
                  <span
                    className="flex h-10 w-10 items-center justify-center bg-gold text-ground"
                    aria-hidden
                  >
                    <IconStar className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="font-[family-name:var(--font-display)] text-lg tracking-tight text-ink">
                      We name who stood out
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                      The committee gathers what the year revealed: strong
                      delivery, quiet leadership, team excellence, and the
                      moments that lifted the companies. Award descriptions and
                      criteria are published so everyone can see the standard;
                      shortlists appear only on personal ballots.
                    </p>
                  </div>
                </li>
                <li className="grid grid-cols-[auto_1fr] gap-4">
                  <span
                    className="flex h-10 w-10 items-center justify-center bg-gold text-ground"
                    aria-hidden
                  >
                    <IconMail className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="font-[family-name:var(--font-display)] text-lg tracking-tight text-ink">
                      You get a personal invitation
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                      When voting opens, eligible colleagues receive a private
                      link by email. Your ballot is yours alone. There is no
                      shared public form to pass around.
                    </p>
                  </div>
                </li>
                <li className="grid grid-cols-[auto_1fr] gap-4">
                  <span
                    className="flex h-10 w-10 items-center justify-center bg-gold text-ground"
                    aria-hidden
                  >
                    <IconBallot className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="font-[family-name:var(--font-display)] text-lg tracking-tight text-ink">
                      The room decides together
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                      Some categories blend executive and staff voices so
                      performance and leadership both count. Others are decided
                      by colleagues alone, from a shortlist or by open choice.
                      When the window closes, results are published for
                      everyone to see.
                    </p>
                  </div>
                </li>
              </ol>
              {current ? (
                <Link
                  href={`/${current.year}/awards`}
                  className="thread-link mt-10 inline-flex font-[family-name:var(--font-label)] text-xs font-semibold uppercase tracking-[0.14em] text-gold"
                >
                  Browse {current.year} awards
                </Link>
              ) : null}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
          <div className="axial-rule mb-10" />
          <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-ink">
            Award families
          </h2>
          <p className="mt-3 max-w-prose text-sm leading-relaxed text-ink-muted">
            Each category has its own description and judging criteria on the
            award page. Here is the shape of the season.
          </p>
          <ul className="mt-10 grid gap-6 sm:grid-cols-2">
            <li className="stage-panel p-5">
              <div className="flex items-center gap-3 text-gold">
                <IconUsers className="h-6 w-6" />
                <h3 className="font-[family-name:var(--font-display)] text-lg text-ink">
                  People of the year
                </h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                Employee of the Year, Supervisor of the Year, Rookie of the Year,
                Excellent Leadership, Pioneer Award for Innovation, and Steeze
                Under Pressure.
              </p>
            </li>
            <li className="stage-panel p-5">
              <div className="flex items-center gap-3 text-gold">
                <IconBuilding className="h-6 w-6" />
                <h3 className="font-[family-name:var(--font-display)] text-lg text-ink">
                  Teams and culture
                </h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                Department of the Year plus General favourites such as Best
                Dressed, Foodie of the Year, and Employees&apos; Choice of the
                Year, the open popular vote for the colleague people most enjoy
                working with.
              </p>
            </li>
          </ul>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-24 sm:px-8">
          <div className="axial-rule mb-10" />
          <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-ink">
            Past seasons
          </h2>
          <p className="mt-2 max-w-prose text-sm text-ink-muted">
            Earlier years stay available for reading criteria and published
            results.
          </p>
          {archive.length === 0 ? (
            <p className="mt-8 text-sm text-ink-muted">
              {current
                ? `${current.year} is the first published season (${yearStatusLabel(current.status)}).`
                : "Seasons will appear here as years are published."}
            </p>
          ) : (
            <ul className="mt-8 flex flex-wrap gap-4">
              {archive.map((y) => (
                <li key={y.year}>
                  <Link
                    href={`/${y.year}`}
                    className="thread-link font-[family-name:var(--font-display)] text-xl text-gold-bright"
                  >
                    {y.year}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </>
  );
}
