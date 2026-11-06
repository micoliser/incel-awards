import Image from "next/image";
import type { Division } from "@/lib/types";

type LogoProps = {
  className?: string;
  /** Height in pixels; width follows each asset’s aspect ratio. */
  size?: number;
};

/** Icon-only Global mark (no wordmark) — use in the site header. */
export function BrandMark({ className = "", size = 56 }: LogoProps) {
  return (
    <Image
      src="/global-favicon.png"
      alt="Incel Group"
      width={size}
      height={Math.round(size * (302 / 281))}
      className={`object-contain ${className}`}
      priority
    />
  );
}

/** Full Global wordmark — section headers and body. */
export function GlobalLogo({ className = "", size = 48 }: LogoProps) {
  const height = size;
  const width = Math.round(height * (1497 / 567));
  return (
    <Image
      src="/global-logo.png"
      alt="Incel Global"
      width={width}
      height={height}
      className={`object-contain ${className}`}
    />
  );
}

/** Tourism wordmark — section headers and body. */
export function TourismLogo({ className = "", size = 48 }: LogoProps) {
  const height = size;
  const width = Math.round(height * (382 / 159));
  return (
    <Image
      src="/tourism-logo.png"
      alt="Incel Tourism"
      width={width}
      height={height}
      className={`object-contain ${className}`}
    />
  );
}

/** Tourism logo for Tourism; Global logo for Global and General. */
export function DivisionLogo({
  division,
  size = 48,
  className = "",
}: LogoProps & { division: Division }) {
  if (division === "tourism") {
    return <TourismLogo size={size} className={className} />;
  }
  return <GlobalLogo size={size} className={className} />;
}
