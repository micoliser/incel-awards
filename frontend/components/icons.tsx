import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { title?: string };

function baseProps({ title, ...props }: IconProps) {
  return {
    width: 24,
    height: 24,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.5,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": title ? undefined : true,
    role: title ? ("img" as const) : undefined,
    ...props,
  };
}

export function IconStar(props: IconProps) {
  const { title, ...rest } = props;
  return (
    <svg {...baseProps(props)}>
      {title ? <title>{title}</title> : null}
      <path d="M12 3.2 14.2 8.6l5.8.5-4.4 3.7 1.4 5.6L12 15.7 6.9 18.4l1.4-5.6L4 9.1l5.8-.5L12 3.2Z" />
    </svg>
  );
}

export function IconUsers(props: IconProps) {
  return (
    <svg {...baseProps(props)}>
      {props.title ? <title>{props.title}</title> : null}
      <circle cx="9" cy="8" r="2.5" />
      <path d="M3.5 18.5c.6-2.6 2.7-4 5.5-4s4.9 1.4 5.5 4" />
      <circle cx="16.5" cy="9" r="2" />
      <path d="M14.2 14.2c1.7.4 3 1.4 3.6 3.3" />
    </svg>
  );
}

export function IconBuilding(props: IconProps) {
  return (
    <svg {...baseProps(props)}>
      {props.title ? <title>{props.title}</title> : null}
      <path d="M4 20V6.5L12 3l8 3.5V20" />
      <path d="M9 20v-5h6v5" />
      <path d="M8 9h1.5M14.5 9H16M8 12.5h1.5M14.5 12.5H16" />
    </svg>
  );
}

export function IconCompass(props: IconProps) {
  return (
    <svg {...baseProps(props)}>
      {props.title ? <title>{props.title}</title> : null}
      <circle cx="12" cy="12" r="8" />
      <path d="m15.5 8.5-2.2 5.8-5.8 2.2 2.2-5.8 5.8-2.2Z" />
    </svg>
  );
}

export function IconGlobe(props: IconProps) {
  return (
    <svg {...baseProps(props)}>
      {props.title ? <title>{props.title}</title> : null}
      <circle cx="12" cy="12" r="8" />
      <path d="M4.5 12h15M12 4c2.4 2.4 3.6 5 3.6 8s-1.2 5.6-3.6 8c-2.4-2.4-3.6-5-3.6-8s1.2-5.6 3.6-8Z" />
    </svg>
  );
}

export function IconThread(props: IconProps) {
  return (
    <svg {...baseProps(props)}>
      {props.title ? <title>{props.title}</title> : null}
      <path d="M4 7h16M4 12h16M4 17h16" />
      <path d="M7 4v16M12 4v16M17 4v16" opacity="0.45" />
    </svg>
  );
}

export function IconBallot(props: IconProps) {
  return (
    <svg {...baseProps(props)}>
      {props.title ? <title>{props.title}</title> : null}
      <rect x="4.5" y="3.5" width="15" height="17" rx="1" />
      <path d="m8 11 2.2 2.2L15.5 8" />
      <path d="M8 16h8" />
    </svg>
  );
}

export function IconMail(props: IconProps) {
  return (
    <svg {...baseProps(props)}>
      {props.title ? <title>{props.title}</title> : null}
      <rect x="3.5" y="5.5" width="17" height="13" rx="1" />
      <path d="m4.5 7.5 7.5 5.5 7.5-5.5" />
    </svg>
  );
}
