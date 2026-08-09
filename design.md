# HR Recruitment Design System

Adapted from the HP visual language for the **Internal Recruitment System** (Thai UI). The product sits on **pure white** (`{colors.canvas}` — `#ffffff`) with thin gray panels (`{colors.cloud}` / `{colors.fog}`) for alternating section bands. There is one chromatic action color — **Electric Blue** (`{colors.primary}` — `#024ad8`) — and one ink color (`{colors.ink}` — `#1a1a1a`); together they do ninety percent of the work.

Type is a single Thai-capable family across every surface: **TH Sarabun New**, loaded from local static fonts, set at weight 500 for headlines and 400 for body.

The signature gesture is **angular blue chevrons** — sharp 0-radius slashes used as a hero-only motif. Outside those decorative slashes, every other surface is rectilinear with **soft 8–16px corners** on cards and a 4px corner on buttons.

**Key Characteristics:**
- Pure white canvas (`{colors.canvas}`) with deep ink (`{colors.ink}`) running every body surface; light fog bands alternate for section rhythm.
- Electric Blue (`{colors.primary}`) is the lone CTA fill and link color; it appears at most twice per viewport.
- TH Sarabun New across every surface — display, body, button, caption (Thai + Latin).
- Cards round at `{rounded.xl}` (16px); buttons sit at `{rounded.md}` (4px) with **sentence-case Thai labels** (no uppercase).
- App shell rhythm: **vertical sidebar** → utility-strip → white body → cloud-band → ink slab → ink footer.

---

## Colors

### Brand & Accent
- **Electric Blue** (`{colors.primary}` — `#024ad8`): Primary CTA fill, link color, chevron-decoration fill, active nav indicator.
- **Bright Blue** (`{colors.primary-bright}` — `#296ef9`): Lighter variant used inside dark slabs.
- **Deep Navy** (`{colors.primary-deep}` — `#0e3191`): Pressed state for the primary CTA.
- **Soft Blue** (`{colors.primary-soft}` — `#c9e0fc`): Pale-blue surface / hover wash.

### Surface
- **Canvas** (`{colors.canvas}` — `#ffffff`): Universal page background.
- **Paper** (`{colors.paper}` — `#ffffff`): Card surfaces (with hairline borders or shadows).
- **Cloud** (`{colors.cloud}` — `#f7f7f7`): Lightest gray section band; sidebar background.
- **Fog** (`{colors.fog}` — `#e8e8e8`): Slightly darker gray surface band (utility strip, dividers).
- **Steel** (`{colors.steel}` — `#c2c2c2`): Hairline border for stronger emphasis.
- **Bloom Coral** (`{colors.bloom-coral}` — `#ff5050`): Alert / sale-tag chip (use sparingly).

### Text
- **Ink** (`{colors.ink}` — `#1a1a1a`): Universal text color on white surfaces.
- **Ink Deep** (`{colors.ink-deep}` — `#000000`): Pure black for wordmark/strokes.
- **On Ink** (`{colors.on-ink}` — `#ffffff`): Pure white used for text on dark slabs.
- **Charcoal** (`{colors.charcoal}` — `#3d3d3d`): Muted body color (secondary descriptions).
- **Graphite** (`{colors.graphite}` — `#636363`): Smaller-print color (legal, metadata, sidebar labels).

---

## Typography

**Font Family:** TH Sarabun New (Fallbacks: Sarabun, sans-serif).

**Source files** (app static):

| File | Weight | Style |
|---|---|---|
| `recruitment/static/fonts/THSarabunNew.ttf` | 400 | normal |
| `recruitment/static/fonts/THSarabunNew-Italic.ttf` | 400 | italic |
| `recruitment/static/fonts/THSarabunNew-Bold.ttf` | 500 / 600 / 700 | normal |
| `recruitment/static/fonts/THSarabunNew-BoldItalic.ttf` | 700 | italic |

*Notes:*
- UI language is Thai (`lang="th"`). Prefer sentence case; do **not** force `text-transform: uppercase` on Thai labels.
- Sarabun reads small — body defaults are larger than Latin-only systems. Keep body line-height ≥ 1.5 and display line-height ≈ 1.15.
- Medium (500) maps to Bold file when no dedicated Medium cut exists.

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| `{typography.display-xxl}` | 72px | 500 | 1.15 | 0 | Hero brand / display |
| `{typography.display-xl}` | 56px | 500 | 1.15 | 0 | Section headlines |
| `{typography.display-sm}` | 28px | 500 | 1.25 | 0 | Card / step titles |
| `{typography.body-md}` | 20px | 400 | 1.5 | 0 | Default body |
| `{typography.caption-md}` | 18px | 400 | 1.5 | 0 | Specs, metadata, nav labels |
| `{typography.button-md}` | 18px | 600 | 1.4 | 0.2px | Button labels (sentence case) |

**CSS implementation:** `@font-face` + tokens live in `recruitment/static/recruitment/css/design.css`.

---

## Layout & Spacing

- **Base unit**: 8px (Smaller half-step at 4px).
- **Section padding**: 80px (`{spacing.section}`) vertical between major bands on desktop; collapses to ~48px on mobile.
- **Card internal padding**: 24px (`{spacing.xl}`) for product cards; 32px (`{spacing.xxl}`) for promo strips.
- **Content max-width**: 1366px desktop.
- **Sidebar width**: 260px (`{layout.sidebar-width}`), sticky full viewport height.
- **App shell**: CSS grid — `sidebar | main frame` on desktop; collapsible off-canvas sidebar + backdrop below 900px.
- **Grid**: 4 columns (>1200px), 3 (1024-1199px), 2 (768-1023px), 1 (<768px).

### Navigation
- **Vertical navbar** (primary): Workspace + Hiring groups; active item uses canvas fill + 3px inset Electric Blue bar.
- **Utility strip**: thin fog band above main content (phase label + mobile menu toggle).
- **Top horizontal nav**: not used in this product shell.

---

## Elevation & Depth

| Level | Treatment | Use |
|---|---|---|
| 0 — Flat | No border, no shadow | Section bands, sidebar, full-bleed photos |
| 1 — Hairline | 1px solid `#e8e8e8` | Outlined buttons, table cells, sidebar edge |
| 2 — Soft Lift | `0 2px 8px rgba(26, 26, 26, 0.08)` | Product cards, pricing tiers |
| 3 — Floating Modal | `0 8px 24px rgba(26, 26, 26, 0.12)` | Drawers, mobile sidebar sheet |

---

## Shapes (Border Radius)

| Token | Value | Use |
|---|---|---|
| `{rounded.none}` | 0px | Hero chevron decorations, full-bleed photos |
| `{rounded.md}` | 4px | Primary buttons, secondary buttons, text inputs, nav items |
| `{rounded.lg}` | 8px | Badge pills, category-icon cards |
| `{rounded.xl}` | 16px | Product cards, workflow lists, photo frames |
| `{rounded.pill}` | 9999px | Category tabs, search-pill input |

---

## Components

### Buttons
- **`button-primary`**: Background `#024ad8`, text `#ffffff`, sentence case, 600 weight, 4px radius.
- **`button-outline`**: Background `#ffffff`, text `#024ad8`, 1px `#024ad8` border, 4px radius.
- **`button-ink`**: Background `#1a1a1a`, text `#ffffff`, 4px radius (Used on dark photo overlays).
- **`button-block`**: Full-width variant (e.g. sidebar Sign in).

### Cards
- **`card-product`**: Background `#ffffff`, 16px radius, 24px padding, Soft Lift shadow.
- **`card-product-feature`**: Background `#f7f7f7`, 16px radius, 32px padding (no shadow).

### Inputs
- **`text-input`**: Background `#ffffff`, 4px radius, 1px `#c2c2c2` border. Gains 1px `#1a1a1a` border on focus.

### Sidebar
- Background `{colors.cloud}`; brand + grouped links + footer CTA.
- Active link: `{colors.canvas}` background, `{colors.primary}` text, 3px left inset bar.

---

## Do's and Don'ts

### Do
- Reserve `{colors.primary}` (`#024ad8`) for the primary CTA, links, active nav, and chevron motifs (max 2 strong blue accents per viewport).
- Use `{rounded.xl}` (16px) for cards/photos and `{rounded.md}` (4px) for buttons/inputs. Keep this strict two-tier split.
- Close every page with a dark `{colors.ink}` footer slab.
- Use **TH Sarabun New** from `recruitment/static/fonts/` for all UI text; keep Thai sentence case on buttons and nav.
- Apply Soft Lift shadow *only* to product cards and pricing tiers.

### Don't
- Don't round buttons above 4px; they must remain sharp.
- Don't use the chevron decoration as inline noise; it is a hero-only element.
- Don't apply heavy material shadows to section bands.
- Don't use full-bleed circular masks for photography (use 16px rounded frames instead).
- Don't load remote Latin-only webfonts (e.g. Manrope / Inter) as the primary family — Thai UI depends on local Sarabun.
- Don't force `uppercase` on Thai button or nav labels.
