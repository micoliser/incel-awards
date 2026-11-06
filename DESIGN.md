---
name: Incel Group Employee Awards
description: Dark gala-stage awards site for Tourism + Global recognition seasons
colors:
  ground: "#07090f"
  ground-deep: "#0e1320"
  ink: "#f4f1ea"
  ink-muted: "#9aa3b5"
  indigo: "#3d5a8a"
  indigo-deep: "#151c2e"
  gold: "#d4a84b"
  gold-bright: "#f0d078"
  teal: "#3d9b7a"
  tourism: "#3d9b7a"
  global: "#5b7fb5"
  shared: "#c4a35a"
  surface: "#121826"
typography:
  display:
    fontFamily: "Syne, ui-sans-serif, sans-serif"
    fontSize: "3rem"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Commissioner, ui-sans-serif, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0em"
  label:
    fontFamily: "Archivo, ui-sans-serif, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.16em"
rounded:
  none: "0px"
  sm: "2px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "32px"
  xl: "64px"
components:
  button-primary:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.ground}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "12px 24px"
  button-primary-hover:
    backgroundColor: "{colors.gold-bright}"
    textColor: "{colors.ground}"
  award-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "20px"
---

# Design System — Incel Group Employee Awards

## Overview

Public awards surfaces read as a **gala stage night**: deep charcoal ground, gold spotlight, indigo structure, teal Tourism plane. Brand (Incel Group) leads the first viewport with a gold shimmer title; Employee Awards is the offer. Operate screens (catalogue, ballot, audit) inherit the same tokens with quieter motion.

Scene: awards ceremony / stage lighting — dark ground by intent, not generic “dark mode SaaS.”

## Colors

| Token | Hex | Role |
|---|---|---|
| ground | `#07090f` | Stage night atmosphere |
| indigo / indigo-deep | `#3d5a8a` / `#151c2e` | Structure, Global plane, countdown “opens” |
| gold / gold-bright | `#d4a84b` / `#f0d078` | Primary CTA, focus, thread underline, brand shimmer |
| teal / tourism | `#3d9b7a` | Tourism division + “voting” status |
| shared | `#c4a35a` | Company-wide plane |
| ink / ink-muted | `#f4f1ea` / `#9aa3b5` | Body and secondary text on dark |
| surface | `#121826` | Panels and award cards |

Avoid purple neon glow, cream+terracotta, and broadsheet hairline density. Gold accents stay warm metal, not magenta.

## Typography

- **Display:** Syne — brand, season titles, award names
- **Body:** Commissioner — reading measure ~65–75ch
- **Label:** Archivo — uppercase tracked meta (division, status, CTA labels)

No Inter / Roboto / Arial / system as the design voice.

## Layout

- Max content width ~72rem (`max-w-6xl`)
- Home first viewport: full-bleed hero photograph under stage gradient + gold spotlight; brand → headline → support → gold CTA. No card grid or stats in the hero.
- Year hub: weave-ground + axial rules; division sections with color planes
- Catalogue / ballot / results: stage panels (`stage-panel`) instead of white cards

## Elevation & Depth

Stage panels use a thin gold-tinted rule and soft depth shadow. Award surfaces lift slightly on hover. Spotlight radial and drifting sash band carry atmosphere — not purple glow halos.

## Motion

- Staggered `weft-in` entrances on hero and key titles
- Drifting `weave-band` sash; gold text shimmer on brand/season titles
- Soft spotlight pulse behind hero brand
- Trophy nudge on award-card hover
- Respect `prefers-reduced-motion`

## Shapes

Mostly square (ceremonial, not soft SaaS pills). Status badges use `2px` radius only. Primary buttons are square gold fills.

## Components

- **Site header:** brand + gold “Employee Awards” eyebrow; glass dark bar; weave-band underline
- **Award surface:** top division color plane, gold meta, trophy hover motion
- **Year status badge:** status-toned chip on dark
- **Thread link:** gold underline scales in on hover/focus
- **Vote / results:** Tokenized ballot and published results inherit stage panels and gold CTA language; no live tallies on the vote page

## Do's and Don'ts

**Do**

- Lead with Incel Group at hero scale on marketing surfaces
- Encode Tourism / Global / Shared as flat color planes
- Keep ballot entry token-gated (email link only)
- Prefer fixture/API data for award fields — no slug special-cases
- Keep Operate screens scannable; flash lives in chrome and hero, not form noise

**Don't**

- Meme / “incel-internet” aesthetics
- Purple gradients, cream+terracotta cliché, broadsheet editorial costume
- Card soup or eyebrow kickers crowding the first viewport
- Thick side-tab accent borders on cards
- Live tallies on the vote page during voting
- Zero-offset colored glow as the only hierarchy signal
