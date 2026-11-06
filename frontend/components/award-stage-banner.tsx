import Image from "next/image";
import { divisionCompanyName } from "@/lib/format";
import type { Division } from "@/lib/types";

type AwardStageBannerProps = {
  title: string;
  division: Division;
};

export function AwardStageBanner({ title, division }: AwardStageBannerProps) {
  return (
    <div className="relative mt-5 aspect-[16/11] w-full overflow-hidden border border-gold/25 sm:aspect-[16/9]">
      <Image
        src="/images/award-stage-banner.jpg"
        alt=""
        fill
        priority
        className="object-cover object-center"
        sizes="(max-width: 768px) 100vw, 768px"
      />
      <div
        className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/20 to-black/35"
        aria-hidden
      />
      <div className="absolute inset-0 flex flex-col items-center justify-center px-6 pb-[12%] pt-4 text-center sm:px-10 sm:pb-[10%]">
        <h1 className="animate-weft max-w-[18ch] font-[family-name:var(--font-display)] text-2xl font-semibold leading-tight tracking-tight text-ink drop-shadow-[0_2px_16px_rgba(0,0,0,0.7)] sm:max-w-[22ch] sm:text-3xl md:text-4xl">
          {title}
        </h1>
        <p className="animate-weft animate-weft-delay-1 mt-2 font-[family-name:var(--font-label)] text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-bright drop-shadow-[0_1px_8px_rgba(0,0,0,0.6)] sm:mt-3 sm:text-xs">
          {divisionCompanyName(division)}
        </p>
      </div>
    </div>
  );
}
