---
name: Klim
description: A calm, exact B-BBEE scorecard estimator for accountants and consultants, in a light zinc shell with a deep green accent.
colors:
  primary: "#18181b"
  primary-hover: "#27272a"
  primary-active: "#09090b"
  accent: "#166534"
  accent-hover: "#14532d"
  accent-soft: "#166534"
  accent-tint: "#f3faf6"
  accent-tint-2: "#d7eee3"
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

Klim is a working tool for accountants and consultants who score clients' B-BBEE certificates. The shell is a light dashboard: zinc-50 canvas, zinc-100 step rail, white cards, a near-black primary button, and a deep green accent for links, focus, selection and progress fills. Inputs keep a soft glass tint. Radii stay 16 to 24px, and each step still fades in. The numbers stay the point: Geist with tabular figures, right-aligned in fields and tables.

Light only. The owner rejected a dark, gold-accented look. The light shell is the alabaster role of that dashboard (paper and a quiet step list), drawn with the zinc neutrals above, not a second warm palette and not the charcoal theme.

**Key Characteristics:**
- Zinc neutrals, white cards, near-black primary, deep green accent.
- Geist throughout with tabular figures; tight negative tracking on headings.
- Glass inputs: a 4% ink tint that turns green on focus.
- 16px controls, 24px cards, hairline borders.
- Each step's title, intro, cards and footer rise in sequence (fade, 12px slide, blur to sharp).
- Scorecard steps sit in a sober rail. Under 900px that rail collapses into a dialog.

## Colors

### Primary
- **Ink Button** (#18181b): primary buttons, the current-step disc, checkmarks, the ladder marker, tab underline. Hover #27272a, pressed #09090b.

### Accent
- **Deep green** (#166534, hover #14532d): links, the focus outline, progress fills. #166534 is 7.130:1 on #ffffff, 6.831:1 on canvas #fafafa, and 6.487:1 on the rail #f4f4f5 (WCAG 2.1 relative luminance). Hover #14532d is 9.111:1 on #ffffff.
- **Focus ring:** `0 0 0 2px #ffffff, 0 0 0 4px #166534`. The green stroke is the same 7.130:1 against white, above the 3:1 non-text bar.
- **Green wash** (#f3faf6, #d7eee3): selection, the achieved band on the level ladder, selected rows. #166534 on those washes is 6.728:1 and 5.850:1.

### Neutral
- **Canvas** (#fafafa), **Rail** (#f4f4f5), **Card** (#ffffff), **Hairline** (#e4e4e7 / #d4d4d8).
- **Ink** (#09090b), **Ink 2** (#3f3f46), **Ink 3** (#71717a).

### State
- Success #15803d, Warning #a16207, Danger #b91c1c, Info #1d4ed8, each on its pale tint with an icon and a written title.

### Named Rules
**The Two Voices Rule.** Near-black says "do this next"; deep green says "you can go here" or "you are here". Neither decorates.

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

A 60px top bar (brand, client, scorecard chip, unsaved state, Open/Save), a 264px sticky step rail, and a centred main column up to 880px (results up to 1040px). Under 900px the rail is hidden until a full-width "Step n of m" button opens it as a dialog; Escape, Close steps, or the dimmed page closes it and returns focus to that button. Under 640px Continue shortens to "Continue". From 360 to 430px the results summary stacks in one column and each element tile is full width. Grid children use `minmax(0, 1fr)` so wide tables scroll inside their card.

## Elevation & Depth

Flat with faint lift. Cards carry `0 1px 2px rgb(9 9 11 / 0.04), 0 1px 3px rgb(9 9 11 / 0.05)`; hover lift `0 4px 12px -2px rgb(9 9 11 / 0.06)`; menus `0 16px 32px -8px rgb(9 9 11 / 0.14)`.

## Shapes

Controls 16px, cards 24px, chips and segments 10px, switches and badges fully round. 1px hairlines; no coloured side stripes.

## Components

### Buttons
44px tall (36px small), 16px radius. Primary: near-black with white text. Secondary: white with a hairline. Ghost: no fill, faint ink wash on hover. Focus shows the green ring.

### Inputs
48px, glass fill rgb(9 9 11 / 0.04), hairline border, 16px radius, 16px side padding. Focus: border #166534, fill rgb(22 101 52 / 0.08), green ring. Numbers right-aligned with R, %, or "people" affixes. Disabled: rail grey, muted text, not-allowed cursor.

### Cards
White, 24px radius, hairline, rest shadow.

### Step rail
A sober scorecard list under a "Scorecard" label. Each row has a number, a check, or a lock, plus the words Current, Done, or Needs attention, so state is not colour alone. The current row is a white chip with a hairline and a near-black disc. A done row keeps the check and a green disc. Locked rows are muted and show a lock. Under 900px the same list is a dialog titled by the Steps label, with a 44px Close steps control.

### Results bento
On the Scorecard tab, one tile per element. Each tile shows the element name (the existing link back to that step), points and maximum, points still open or "At maximum", and a sub-minimum line read from the checks already returned: "Sub-minimum met", "Sub-minimum missed", or "No sub-minimum", each with an icon. A thin meter repeats the points and is hidden from assistive tech. Tiles stay equal width; from 360 to 430px they stack in one column and the figures wrap instead of clipping.

### Level ladder (signature)
Bands from Non-compliant to Level 1 sized by their thresholds; a green wash fills to the score and a near-black marker carries the points. The scale is inset so the points label stays inside the card.

### Motion
`fadeSlideIn`: opacity 0, blur 4px, translateY 12px to rest, 0.6s cubic-bezier(0.16, 1, 0.3, 1). Delays: title 0.05s, intro 0.12s, cards 0.2s / 0.28s / 0.36s / 0.44s, footer 0.5s. Off under prefers-reduced-motion.

## Do's and Don'ts

### Do:
- **Do** keep one near-black primary action per screen.
- **Do** use deep green only for links, focus, selection and progress fills.
- **Do** give every state notice an icon and a title.
- **Do** show the clause beside each target.

### Don't:
- **Don't** use a dark theme or gold accents.
- **Don't** add gradient text, eyebrows, emoji icons, or invented testimonials.
- **Don't** use colour as the only signal of a state.
- **Don't** add coloured left stripes thicker than 1px.
