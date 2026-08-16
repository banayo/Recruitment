# 🎨 HR Recruitment Design System

Adapted from the HP visual language for the **Internal Recruitment System**. The product sits on a **pure white** canvas (`{colors.canvas}` — `#ffffff`) with thin gray panels (`{colors.cloud}` / `{colors.fog}`) for alternating section bands. 

There is one chromatic action color — **Electric Blue** (`{colors.primary}` — `#024ad8`) — and one ink color (`{colors.ink}` — `#1a1a1a`); together they do ninety percent of the work.

Type is a single Thai-capable family across every surface: **TH Sarabun New**, loaded from local static fonts, set at weight 500 for headlines and 400 for body.

**Key Characteristics:**
- **Clean Canvas:** Pure white canvas (`{colors.canvas}`) with deep ink (`{colors.ink}`) running every body surface; light fog bands alternate for section rhythm.
- **Focused Actions:** Electric Blue (`{colors.primary}`) is the lone CTA fill and link color; it appears at most twice per viewport.
- **Single Typography:** TH Sarabun New across every surface — display, body, button, caption. (No forced uppercase for Thai labels).
- **Shapes & Radii:** Cards round at `{rounded.xl}` (16px); buttons and inputs sit at `{rounded.md}` (4px).
- **App Shell Rhythm:** Vertical sidebar → utility-strip → white body → cloud-band → ink slab → ink footer.

---

## 1. Colors

### 🔵 Brand & Accent
- **Electric Blue** (`{colors.primary}` — `#024ad8`): Primary CTA fill, link color, active nav indicator.
- **Bright Blue** (`{colors.primary-bright}` — `#296ef9`): Lighter variant used inside dark slabs.
- **Deep Navy** (`{colors.primary-deep}` — `#0e3191`): Pressed state for the primary CTA.
- **Soft Blue** (`{colors.primary-soft}` — `#c9e0fc`): Pale-blue surface / hover wash.

### ⚪️ Surface
- **Canvas** (`{colors.canvas}` — `#ffffff`): Universal page background.
- **Paper** (`{colors.paper}` — `#ffffff`): Card surfaces (with hairline borders or shadows).
- **Cloud** (`{colors.cloud}` — `#f7f7f7`): Lightest gray section band; sidebar background.
- **Fog** (`{colors.fog}` — `#e8e8e8`): Slightly darker gray surface band (utility strip, dividers).
- **Steel** (`{colors.steel}` — `#c2c2c2`): Hairline border for stronger emphasis.

### 🟢 Status Colors (HR Workflow)
- **Warning** (`#f59e0b`): Amber/Yellow — For *Pending Manager Approval* status.
- **Info** (`#8b5cf6`): Purple — For *Manager Approved (Waiting for HR)* status.
- **Success** (`#10b981`): Green — For *HR Approved / Completed* status.
- **Danger / Bloom Coral** (`#ff5050`): Red — For *Rejected / Cancelled* status.

### ⚫️ Text
- **Ink** (`{colors.ink}` — `#1a1a1a`): Universal text color on white surfaces.
- **On Ink** (`{colors.on-ink}` — `#ffffff`): Pure white used for text on dark slabs or primary buttons.
- **Charcoal** (`{colors.charcoal}` — `#3d3d3d`): Muted body color (secondary descriptions).
- **Graphite** (`{colors.graphite}` — `#636363`): Smaller-print color (legal, metadata, sidebar labels).

---

## 2. Typography

**Font Family:** TH Sarabun New (Fallbacks: Sarabun, sans-serif).

*Notes: Sarabun reads small — body defaults are larger than Latin-only systems. Keep body line-height ≥ 1.5.*

| Token | Size | Weight | Line Height | Use |
| :--- | :--- | :--- | :--- | :--- |
| `{typography.display-xl}` | 56px | 500 | 1.15 | Section headlines |
| `{typography.display-sm}` | 28px | 500 | 1.25 | Card / step titles |
| `{typography.body-md}` | 20px | 400 | 1.5 | Default body / table data |
| `{typography.caption-md}` | 18px | 400 | 1.5 | Specs, metadata, nav labels |
| `{typography.button-md}` | 18px | 600 | 1.4 | Button labels (sentence case) |

---

## 3. Shapes & Elevation

### Border Radius
- `{rounded.md}` (4px): Primary buttons, secondary buttons, text inputs, nav items.
- `{rounded.xl}` (16px): Product cards, workflow lists, photo frames.
- `{rounded.pill}` (9999px): Status badges, category tabs.

### Elevation & Depth
- **Level 0 (Flat):** No border, no shadow — Section bands, sidebar.
- **Level 1 (Hairline):** 1px solid `#e8e8e8` — Outlined buttons, table cells, sidebar edge.
- **Level 2 (Soft Lift):** `0 2px 8px rgba(26, 26, 26, 0.08)` — **Use ONLY for cards** to lift them off the canvas.

---

## 4. Components

### Buttons
- **Primary:** Background `#024ad8`, text `#ffffff`, 4px radius.
- **Outline:** Background `#ffffff`, text `#024ad8`, 1px `#024ad8` border, 4px radius.
- **Block:** Full-width variant (e.g. sidebar action button).

### Cards
- **Product Card:** Background `#ffffff`, 16px radius, 24px padding, Soft Lift shadow.

### Inputs
- Background `#ffffff`, 4px radius, 1px `{colors.steel}` border. (Gains 1px `{colors.ink}` border on focus).

### Sidebar
- Background `{colors.cloud}`.
- **Active link:** `{colors.canvas}` background, `{colors.primary}` text, 3px left inset Electric Blue bar.

---

## 5. Do's and Don'ts

### ✅ Do
- Reserve `{colors.primary}` (`#024ad8`) for the primary CTA, links, and active nav (max 2 strong blue accents per viewport).
- Use `{rounded.xl}` (16px) for cards and `{rounded.md}` (4px) for buttons/inputs. Keep this strict two-tier split.
- Use **TH Sarabun New** from local static folders for all UI text.
- Apply Soft Lift shadow *only* to product cards.

### ❌ Don't
- Don't round buttons above 4px; they must remain sharp and formal.
- Don't apply heavy material shadows to section bands.
- Don't force `uppercase` on Thai button or nav labels.
- Don't load remote Latin-only webfonts (e.g., Manrope / Inter) as the primary family — the Thai UI depends on local Sarabun.