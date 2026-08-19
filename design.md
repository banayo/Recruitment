# 🎨 HR Recruitment Design System: Premium Glassmorphism

This visual language transforms the **Internal Recruitment System** into a stunning, modern application. It utilizes a fluid mesh-gradient background overlaid with frosted glass panels (`backdrop-filter`), vibrant active colors, and fluid micro-animations.

The core philosophy is **Light & Fluid**: The application feels like it's floating.

---

## 1. Colors & Gradients

### 🌌 Backgrounds
- **Mesh Canvas:** A fluid gradient of soft blue (`#f0f5ff`), warm pearl (`#fbf8ff`), and soft cyan (`#e0f7fa`) that covers the entire page background.
- **Glass Panel:** `rgba(255, 255, 255, 0.7)` with `backdrop-filter: blur(24px)`. Used for the sidebar, top utility strip, and content cards.
- **Solid Canvas (Fallback):** `#f8fafc` if backdrop-filter is not supported.

### 🟣 Brand & Vibrant Accents
- **Primary Gradient:** A vibrant horizontal gradient from `#4f46e5` (Indigo) to `#06b6d4` (Cyan). Used for primary buttons and hover states.
- **Primary Solid:** `#4f46e5`. Used for active navigation lines or single-color icons.
- **Soft Accent:** `rgba(79, 70, 229, 0.08)`. Used for hover states on list items and secondary buttons.

### 🟢 Status Colors (Glowing Variants)
- **Pending (Warning):** Background `#fef3c7`, Text `#b45309`, Border `#fde68a`.
- **Approved / Success:** Background `#d1fae5`, Text `#047857`, Border `#a7f3d0`.
- **In Progress / Info:** Background `#e0e7ff`, Text `#4338ca`, Border `#c7d2fe`.
- **Rejected (Danger):** Background `#ffe4e4`, Text `#c53030`, Border `#fca5a5`.

### ⚫️ Text & Ink
- **Deep Ink:** `#0f172a` (Slate 900) - Primary text.
- **Charcoal:** `#475569` (Slate 600) - Secondary text, descriptions.
- **Graphite:** `#94a3b8` (Slate 400) - Metadata, disabled text.

---

## 2. Typography

**Font Family:** `Prompt`, sans-serif (Google Fonts).

*Prompt offers a highly legible, geometric, and modern feel that perfectly matches a tech-forward glassmorphic UI.*

| Token | Size | Weight | Line Height | Use |
| :--- | :--- | :--- | :--- | :--- |
| `display-xl` | 48px | 600 | 1.15 | Hero / Major Section headlines |
| `display-sm` | 24px | 600 | 1.25 | Card / Dialog titles |
| `body-md` | 16px | 400 | 1.6 | Default body / table data |
| `caption-md` | 14px | 400 | 1.5 | Specs, metadata, labels |
| `button-md` | 16px | 500 | 1.4 | Button labels |

---

## 3. Shapes, Depth & Glass

### Border Radius
- `8px` (`rounded-lg`): Buttons, inputs, small badges.
- `24px` (`rounded-2xl`): Product cards, dialogs, main content panels, sidebar.
- `9999px` (`rounded-pill`): Status badges.

### Elevation, Glass & Borders
- **Glass Effect:** All surfaces use `rgba(255, 255, 255, 0.65)` with `backdrop-filter: blur(20px)`.
- **Borders:** To make the glass pop, all glass panels have a `1px solid rgba(255, 255, 255, 0.8)` top/left border, and `1px solid rgba(255, 255, 255, 0.3)` bottom/right.
- **Shadow (Lift):** `0 10px 40px -10px rgba(15, 23, 42, 0.08)`. Used on all glass panels to lift them off the background.

---

## 4. Components

### Buttons
- **Primary:** Gradient background (`#4f46e5` to `#06b6d4`), text white, `8px` radius. Smooth scale up (`scale: 1.02`) on hover with a soft shadow.
- **Outline / Glass:** Transparent background, `1px` border of `rgba(79, 70, 229, 0.4)`, text `#4f46e5`. On hover, background fills with soft accent.
- **Danger:** Soft red background (`#fee2e2`), text (`#dc2626`).

### Cards & Panels
- **Glass Panel:** `24px` radius, white translucent background, heavy blur, subtle lifting shadow.

### Inputs
- Background `rgba(255, 255, 255, 0.9)`, `8px` radius, `1px solid #e2e8f0` border.
- **On Focus:** Border becomes `#4f46e5`, and it emits a soft glow `box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.15)`.

### Sidebar
- Floating glass panel (`margin: 16px` from edges).
- **Active link:** Gradient background (`rgba(79,70,229,0.1)`), bold text, with a left inset gradient pill.

---

## 5. Animation (Motion)

- **Hover:** All interactive elements (buttons, cards) must have `transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)`.
- **Focus:** Inputs smoothly transition border colors and ring shadows.
- **Page Load:** Hero sections and panels fade in and slide up slightly (`translateY(10px)` to `0`).
