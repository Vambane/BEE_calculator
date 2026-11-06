---
name: Klim
description: A calm, exact B-BBEE scorecard estimator for accountants and consultants, in a light shadcn-style glass theme.
colors:
  primary: "#18181b"
  primary-hover: "#27272a"
  primary-active: "#09090b"
  accent: "#7c3aed"
  accent-hover: "#6d28d9"
  accent-soft: "#a78bfa"
  accent-tint: "#f5f3ff"
  accent-tint-2: "#ddd6fe"
  canvas: "#fafafa"
  rail: "#f4f4f5"
  surface: "#ffffff"
  line: "#e4e4e7"
  line-strong: "#d4d4d8"
  ink: "#09090b"
  ink-2: "#3f3f46"
  ink-3: "#71717a"
  success: "#15803d"
  warning: "#a16207"
  danger: "#b91c1c"
  info: "#1d4ed8"
typography:
  display:
    fontFamily: "Geist Variable, Geist, system-ui, sans-serif"
    fontSize: "3rem"
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Geist Variable, Geist, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 600
    letterSpacing: "-0.035em"
    lineHeight: 1.2
  title:
    fontFamily: "Geist Variable, Geist, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 650
    lineHeight: 1.3
  body:
    fontFamily: "Geist Variable, Geist, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "\"tnum\" 1"
  label:
    fontFamily: "Geist Variable, Geist, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  sm: "10px"
  md: "16px"
  lg: "24px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "20px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    height: "44px"
    padding: "0 18px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    height: "40px"
    padding: "0 16px"
  button-ghost:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.md}"
    height: "40px"
  input:
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    height: "48px"
    padding: "0 16px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "18px 20px 20px"
  segmented:
    backgroundColor: "{colors.rail}"
    rounded: "{rounded.lg}"
    height: "32px"
  step-current:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
---

# Design System: Klim

## Overview

**Creative North Star: "The Quiet Glass Desk"**

Klim is a working tool for accountants and consultants who score clients' B-BBEE certificates. Its look follows a shadcn-style sign-in theme the owner chose: near-white ground, a near-black primary button, a violet accent for links, focus and fills, soft glass-tinted inputs, generous 16 to 24px radii, and a staggered fade-in as each step opens. The numbers stay the point: Geist with tabular figures, right-aligned in fields and tables.

Light only. The owner rejected a dark, gold-accented look.

**Key Characteristics:**
- Zinc neutrals, white cards, near-black primary, violet accent.
- Geist throughout with tabular figures; tight negative tracking on headings.
- Glass inputs: a 4% ink tint that turns violet on focus.
- 16px controls, 24px cards, hairline borders.
- Each step's title, intro, cards and footer rise in sequence (fade, 12px slide, blur to sharp).

## Colors

### Primary
- **Ink Button** (#18181b): primary buttons, the current-step disc, checkmarks, the ladder marker, tab underline. Hover #27272a, pressed #09090b.

### Accent
- **Violet** (#7c3aed, hover #6d28d9): links.
- **Soft Violet** (#a78bfa): focus borders (at 70%) and the focus outline; the focus ring is rgb(139 92 246 / 0.25).
- **Violet Wash** (#f5f3ff, #ddd6fe): selection, the achieved band on the level ladder, selected rows.

### Neutral
- **Canvas** (#fafafa), **Rail** (#f4f4f5), **Card** (#ffffff), **Hairline** (#e4e4e7 / #d4d4d8).
- **Ink** (#09090b), **Ink 2** (#3f3f46), **Ink 3** (#71717a).

### State
- Success #15803d, Warning #a16207, Danger #b91c1c, Info #1d4ed8, each on its pale tint with an icon and a written title.

### Named Rules
**The Two Voices Rule.** Near-black says "do this next"; violet says "you can go here" or "you are here". Neither decorates.

**The Meaning-Only Rule.** Amber, red and blue appear only for a state the user must understand.

## Typography

**Font:** Geist Variable (fallback system-ui), one family.

### Hierarchy
- **Display** (600, 48px): reserved for a single headline figure.
- **Headline** (600, 32px, -0.035em): step titles (22px under 640px).
- **Title** (600, 18px): card headings.
- **Body** (400, 15px, 1.5): instructions, about 68ch.
- **Label** (500 to 600, 13 to 14px): field labels, table headers, buttons.

**The Tabular Rule.** Body sets tabular numerals; figures line up.

## Layout

A 60px top bar (brand, client, scorecard chip, unsaved state, Open/Save), a 264px sticky step rail, and a centred main column up to 880px. Under 900px the rail becomes a step dropdown with a progress bar; under 640px Continue shortens to "Continue". Grid children use `minmax(0, 1fr)` so wide tables scroll inside their card, with a swipe hint on phones.

## Elevation & Depth

Flat with faint lift. Cards carry `0 1px 2px rgb(9 9 11 / 0.04), 0 1px 3px rgb(9 9 11 / 0.05)`; hover lift `0 4px 12px -2px rgb(9 9 11 / 0.06)`; menus `0 16px 32px -8px rgb(9 9 11 / 0.14)`.

## Shapes

Controls 16px, cards 24px, chips and segments 10px, switches and badges fully round. 1px hairlines; no coloured side stripes.

## Components

### Buttons
44px tall (36px small), 16px radius. Primary: near-black with white text. Secondary: white with a hairline. Ghost: no fill, faint ink wash on hover. Focus shows the violet ring.

### Inputs
48px, glass fill rgb(9 9 11 / 0.04), hairline border, 16px radius, 16px side padding. Focus: border violet at 70%, fill rgb(139 92 246 / 0.08), violet ring. Numbers right-aligned with R, %, or "people" affixes. Disabled: rail grey, muted text, not-allowed cursor.

### Cards
White, 24px radius, hairline, rest shadow.

### Step rail
Done steps show a check, the current step a near-black disc on a white chip, locked steps a lock in muted text.

### Level ladder (signature)
Bands from Non-compliant to Level 1 sized by their thresholds; a violet wash fills to the score and a near-black marker carries the points.

### Motion
`fadeSlideIn`: opacity 0, blur 4px, translateY 12px to rest, 0.6s cubic-bezier(0.16, 1, 0.3, 1). Delays: title 0.05s, intro 0.12s, cards 0.2s / 0.28s / 0.36s / 0.44s, footer 0.5s. Off under prefers-reduced-motion.

## Do's and Don'ts

### Do:
- **Do** keep one near-black primary action per screen.
- **Do** use violet only for links, focus, selection and progress fills.
- **Do** give every state notice an icon and a title.
- **Do** show the clause beside each target.

### Don't:
- **Don't** use a dark theme or gold accents.
- **Don't** add gradient text, eyebrows, emoji icons, or invented testimonials.
- **Don't** use colour as the only signal of a state.
- **Don't** add coloured left stripes thicker than 1px.
