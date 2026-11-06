---
name: BEE Check
description: A calm, exact B-BBEE scorecard estimator for accountants and consultants.
colors:
  primary: "#0f6e5b"
  primary-hover: "#0b5a4a"
  primary-active: "#084a3d"
  primary-tint: "#e5f2ee"
  primary-tint-2: "#cfe7df"
  canvas: "#f3f5f7"
  rail: "#eceff3"
  surface: "#ffffff"
  surface-2: "#f8f9fb"
  line: "#e0e5ea"
  line-strong: "#c9d1d9"
  ink: "#121c26"
  ink-2: "#44515e"
  ink-3: "#5f6b78"
  success: "#08703f"
  success-tint: "#e8f6ee"
  warning: "#8a5400"
  warning-tint: "#fff4e0"
  danger: "#b4231b"
  danger-tint: "#fdf0ef"
  info: "#1a56b8"
  info-tint: "#edf4fe"
typography:
  display:
    fontFamily: "Figtree Variable, Figtree, system-ui, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 750
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Figtree Variable, Figtree, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.2
  title:
    fontFamily: "Figtree Variable, Figtree, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 650
    lineHeight: 1.3
  body:
    fontFamily: "Figtree Variable, Figtree, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "\"tnum\" 1"
  label:
    fontFamily: "Figtree Variable, Figtree, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
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
    height: "40px"
    padding: "0 16px"
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
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    height: "40px"
    padding: "0 12px"
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

# Design System: BEE Check

## Overview

**Creative North Star: "The Working Ledger"**

BEE Check is a working tool for accountants and consultants who score clients' B-BBEE certificates. It sits in the same category as Xero: white working surfaces on a cool grey canvas, one deep green for action, and figures that line up. The interface stays quiet so the numbers, targets and clause references can be read at a glance and checked against the codes.

Density is moderate: a left rail of seven steps, one main column up to 880px wide, and cards that each hold one job. Every figure uses tabular numerals. Colour carries meaning only: green for the next action and progress, amber for sub-minimum risk, red for non-compliance, blue for information. There is no themed world, no illustration and no gradient. The owner rejected a dark, gold-accented look; this system is light-only.

**Key Characteristics:**
- Cool neutral canvas, white surfaces, one green action colour.
- One sans family (Figtree) with tabular figures everywhere.
- 8px radius, hairline borders, soft one-step shadows.
- States always carry a word or icon, never colour alone.
- The printed gap report uses the same tokens on A4.

## Colors

A restrained cool-neutral palette with a single deep green voice and four state colours.

### Primary
- **Ledger Green** (#0f6e5b): primary buttons, the current-step number, checkmarks on completed steps, the level-ladder marker and progress fills. Hover deepens to #0b5a4a, pressed to #084a3d.
- **Green Wash** (#e5f2ee, #cfe7df): selected and filled backgrounds, such as the achieved band on the level ladder.

### Neutral
- **Cool Canvas** (#f3f5f7): the app background behind cards.
- **Rail Grey** (#eceff3): the step rail and the segmented-control track.
- **Paper White** (#ffffff) and **Surface Tint** (#f8f9fb): cards, inputs, table headers, card footers.
- **Hairline** (#e0e5ea) and **Strong Hairline** (#c9d1d9): dividers and input borders.
- **Ink** (#121c26), **Ink 2** (#44515e), **Ink 3** (#5f6b78): headings and figures, body text, secondary text and labels.

### State
- **Success** (#08703f on #e8f6ee), **Warning** (#8a5400 on #fff4e0), **Danger** (#b4231b on #fdf0ef), **Info** (#1a56b8 on #edf4fe). Each is used with a matching icon and a written title.

### Named Rules
**The One Voice Rule.** Ledger Green is the only colour that means "do this next". It never decorates.

**The Meaning-Only Rule.** Amber, red and blue appear only for a state the user must understand: sub-minimum risk, non-compliance, information.

## Typography

**Body and display font:** Figtree Variable (fallback system-ui).

**Character:** A friendly, geometric working sans. One family keeps the tool calm; weight and size carry the hierarchy.

### Hierarchy
- **Display** (750, 40px, 1.05): the recognition level on Results.
- **Headline** (700, 28px): the step title at the top of each page (22px under 640px).
- **Title** (650, 18px): card headings.
- **Body** (400, 15px, 1.5): instructions and notes, kept to about 68ch.
- **Label** (600, 13–14px): field labels, table headers, buttons.

### Named Rules
**The Tabular Rule.** `font-variant-numeric: tabular-nums` is set on the body. Figures in tables and summary tiles must line up.

## Layout

A top bar (60px) holds the brand, client name, scorecard chip, unsaved state and Open/Save. Below it, a 264px left rail lists the seven steps and stays sticky; the main column is centred with a maximum width of 880px and 28–32px padding. Under 900px the rail is replaced by a step dropdown with a progress bar, and padding drops to 16px. Under 640px the Continue button shortens to "Continue". Grid and flex children use `minmax(0, 1fr)` so wide tables scroll inside their card rather than widening the page.

## Elevation & Depth

Mostly flat with tonal layering: canvas, rail and surface are three steps of the same cool neutral. Cards add one soft shadow; popovers use a larger one.

### Shadow Vocabulary
- **Rest** (`0 1px 2px rgb(16 24 40 / 0.06), 0 1px 3px rgb(16 24 40 / 0.08)`): cards and the current step.
- **Raised** (`0 4px 8px -2px rgb(16 24 40 / 0.08), 0 2px 4px -2px rgb(16 24 40 / 0.05)`): hovered interactive surfaces.
- **Pop** (`0 12px 24px -6px rgb(16 24 40 / 0.16), 0 4px 8px -4px rgb(16 24 40 / 0.08)`): menus and the mobile step list.
- **Focus** (`0 0 0 3px rgb(15 110 91 / 0.28)`): every focusable control.

## Shapes

8px is the house radius for buttons, inputs and the current step; cards use 10px; small chips and segment buttons use 6px. Borders are 1px hairlines. No coloured side stripes, no pill-shaped buttons.

## Components

### Buttons
- **Shape:** 8px radius, 40px tall (32px small).
- **Primary:** Ledger Green, white label, 600 weight.
- **Secondary:** white with a strong hairline border.
- **Ghost:** no fill; a faint ink wash on hover.
- **Focus:** the green focus ring; never remove it.

### Inputs / Fields
- **Style:** 40px, white, strong hairline, 8px radius. Numbers are right-aligned, with "R" as a prefix and "%" or "people" as a suffix.
- **Focus:** the border turns green and the focus ring shows.
- **Error:** red border, with the message written below.

### Cards
- White, 10px radius, hairline border, rest shadow, 18–20px padding. A card footer uses Surface Tint.

### Segmented control
- A Rail Grey track with white selected segments. Used for "Indicators / Points" and "Rand amounts / Percentages".

### Navigation (step rail)
- Each step shows a status mark: green check for done, green numbered disc for current, lock for not yet reachable. The current step sits on a white chip with the rest shadow.

### Level ladder (signature)
- A horizontal band from Non-compliant to Level 1, with each level's width set by its points threshold. A green wash fills up to the score, and a green marker carries the points. Tick labels thin out on narrow widths.

## Do's and Don'ts

### Do:
- **Do** use Ledger Green (#0f6e5b) for the one next action on each screen.
- **Do** give every state notice an icon and a written title.
- **Do** show the clause reference beside each target ("cl. 400 2.1.1").
- **Do** keep figures tabular and right-aligned in tables.

### Don't:
- **Don't** use a dark theme or gold accents; the owner rejected that look.
- **Don't** add gradients, gradient text, eyebrows or kicker labels above headings, or emoji icons.
- **Don't** use colour as the only signal of a state.
- **Don't** add a coloured left-border stripe thicker than 1px to cards or notices.
