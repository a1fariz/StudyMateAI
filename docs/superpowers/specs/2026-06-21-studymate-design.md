# StudyMate AI — DESIGN.md
> Adopted Stitch DESIGN.md format. This file is the single source of truth for StudyMateAI's visual identity. AI coding agents read this to generate consistent UI.

---

## 1 · Visual Theme & Atmosphere

**Mood:** Calm, structured, approachable academic energy. Not sterile, not playful — a professional study companion that feels like a well-lit library or a premium notebook.

**Light Academic** — the app lives on warm cream paper surfaces, not cold glass. Depth comes from subtle shadow layering and restrained indigo + teal accents, not heavy blur. Typography is modern sans-serif (Inter + Outfit) for maximum readability during long study sessions.

**Density:** Medium. Comfortable breathing room (24–32px section gaps, 16–20px card padding). Not sparse enough to feel empty, not packed enough to feel claustrophobic.

**Personality keywords:** precise, warm, focused, trustworthy, unhurried.

---

## 2 · Color Palette & Roles

| Token | Hex | Role |
|-------|-----|------|
| `--surface-base` | `#faf9f7` | Page background, default canvas |
| `--surface-raised` | `#ffffff` | Cards, modals, elevated panels |
| `--surface-sunken` | `#f0ece6` | Input backgrounds, inset areas, disabled states |
| `--border-default` | `#d6d4cf` | Default borders, dividers, separators |
| `--border-focus` | `#6366f1` | Focus rings, active inputs |
| `--text-primary` | `#1a1c20` | Headlines, body copy, primary labels |
| `--text-secondary` | `#6b6964` | Muted descriptions, timestamps, metadata |
| `--text-tertiary` | `#a09d97` | Placeholders, disabled text, captions |
| `--accent-primary` | `#6366f1` | Primary buttons, active tabs, links, brand |
| `--accent-secondary` | `#14b8a6` | Success states, secondary actions, "online" indicators |
| `--accent-warn` | `#d97706` | Warnings, caution states |
| `--accent-danger` | `#e11d48` | Errors, destructive actions |
| `--accent-info` | `#6366f1` | Info banners, hints (same as primary) |

**Semantic usage rules:**
- Primary action buttons → `--accent-primary` on `--surface-raised`
- Secondary/outline buttons → `--text-primary` border on `--surface-raised`
- Success confirmations → `--accent-secondary` text/border
- Error states → `--accent-danger` text/border
- Never use pure black (`#000`) or pure white (`#fff`) on large surfaces — always tinted variants above.

---

## 3 · Typography Rules

**Font families:**
- `--font-sans`: `'Inter', system-ui, -apple-system, sans-serif` — all body text, UI chrome, inputs, buttons
- `--font-display`: `'Outfit', 'Inter', system-ui, sans-serif` — headlines, hero text, tab labels, card titles

**Type scale (rem-based, base 16px):**

| Token | Size | Weight | Line-height | Use |
|-------|------|--------|-------------|-----|
| `--text-xs` | 0.75rem (12px) | 400–500 | 1.4 | Captions, badges, metadata |
| `--text-sm` | 0.875rem (14px) | 400–500 | 1.5 | Body text, inputs, buttons |
| `--text-base` | 1rem (16px) | 400–500 | 1.6 | Primary body copy, chat messages |
| `--text-md` | 1.125rem (18px) | 500–600 | 1.5 | Subheadings, card titles |
| `--text-lg` | 1.25rem (20px) | 600–700 | 1.4 | Section headings |
| `--text-xl` | 1.5rem (24px) | 700 | 1.3 | Page titles |
| `--text-2xl` | 2rem (32px) | 700–800 | 1.2 | Hero headline (≤ 40 chars) |
| `--text-3xl` | 2.5rem (40px) | 800 | 1.15 | Marketing hero headline |

**Typography rules:**
- Headlines use `--font-display` (Outfit). Body uses `--font-sans` (Inter).
- Max line-length for body copy: 65ch (approx 620px).
- Headings use tight letter-spacing (`-0.02em` to `-0.03em`).
- Uppercase labels use wider tracking (`0.08em`), small size (`--text-xs`), medium weight.
- Never use more than 3 type sizes in a single component.

---

## 4 · Component Stylings

### 4.1 Buttons

| Variant | Background | Text | Border | Radius | Shadow |
|---------|-----------|------|--------|--------|--------|
| Primary | `--accent-primary` | `#fff` | none | 10px | 0 1px 3px rgba(0,0,0,.08) |
| Secondary | transparent | `--text-primary` | 1px solid `--border-default` | 10px | none |
| Ghost | transparent | `--text-primary` | none | 10px | none |
| Destructive | `--accent-danger` | `#fff` | none | 10px | 0 1px 3px rgba(0,0,0,.08) |

States:
- Default → Hover: lift +2px shadow or +5% opacity
- Active (click): scale 0.97
- Disabled: `--text-tertiary` text, no hover response
- Loading: spinner replaces text, same dimensions

### 4.2 Cards

```
background: --surface-raised
border: 1px solid --border-default
border-radius: 10px
padding: 16px–20px
box-shadow: 0 1px 2px rgba(0,0,0,.04)
```

- Hover: border shifts to `--border-focus` at 40% opacity, shadow increases to `0 2px 8px rgba(0,0,0,.08)`
- No glassmorphism / blur effects. Cards are opaque.
- Max card width: 600px for single-column content; grid cards fill available space.

### 4.3 Inputs

```
background: --surface-sunken
border: 1px solid --border-default
border-radius: 10px
padding: 10px 14px
font-size: --text-sm
```

- Focus: border → `--border-focus`, ring 0 (custom focus style via border only)
- Placeholder: `--text-tertiary`
- Error state: border → `--accent-danger`, subtle error message below in `--text-xs`

### 4.4 Navigation (Tabs)

- Pill shape, `border-radius: 999px` (full round)
- Active: `--accent-primary` background, white text, subtle shadow
- Inactive: transparent background, `--text-secondary` text
- Hover inactive: `--text-primary` text, no background change
- Height: 36–40px, padding: 0 16px

### 4.5 Modals / Overlays

```
background: rgba(250, 249, 247, 0.85)
backdrop-filter: blur(8px)
```

- Panel: `--surface-raised`, 10px radius, padding 24px
- Close button: `--text-secondary`, top-right, 40px touch target

---

## 5 · Layout Principles

**Spacing scale (4px base):**
- 4, 8, 12, 16, 20, 24, 32, 40, 48, 64

**Grid:**
- Max content width: `1200px` (landing), `1400px` (workspace)
- Sidebar: `300px` fixed
- Gutters: 24px desktop, 16px tablet, 12px mobile
- Sections: vertical padding `py-16` (64px) desktop, `py-10` (40px) tablet

**Whitespace philosophy:**
- Generous padding inside cards (≥16px) to let content breathe.
- Section headings get 32–48px bottom margin.
- Related items grouped within 12px gaps; unrelated groups separated by 24px+.

---

## 6 · Depth & Elevation

No glassmorphism. Depth through:

| Layer | Shadow | Z-index |
|-------|--------|---------|
| Flat (cards) | `0 1px 2px rgba(0,0,0,.04)` | base |
| Raised (hover cards) | `0 2px 8px rgba(0,0,0,.08)` | base |
| Overlay (modals) | `0 4px 24px rgba(0,0,0,.12)` | z-50 |
| Dropdown / popover | `0 8px 32px rgba(0,0,0,.14)` | z-40 |
| Navbar sticky | subtle, no elevation change | z-30 |

Surface hierarchy:
- Base: `--surface-base` (#faf9f7)
- Raised: `--surface-raised` (#ffffff)
- Sunken: `--surface-sunken` (#f0ece6)

---

## 7 · Do's and Don'ts

### Do:
- Use `--accent-primary` sparingly — one primary action per viewport.
- Keep card max-width ≤600px for single-column reading (chat, forms).
- Use space, not lines, to separate unrelated sections.
- Maintain 10:1 contrast ratio minimum for body text.
- Round all interactive elements (buttons, inputs, tabs) at 10px or 999px.

### Don't:
- Don't use pure `#000` or `#fff` on large surfaces.
- Don't stack more than 3 accent colors in one viewport.
- Don't use glass blur / backdrop-blur on cards (save for modals only, if needed).
- Don't use font-weight <400 for body text.
- Don't use corners sharper than 4px on interactive elements.
- Don't place text closer than 8px from any border.

---

## 8 · Responsive Behavior

| Breakpoint | Width | Strategy |
|------------|-------|----------|
| Desktop | ≥1024px | Sidebar visible, full grid |
| Tablet | 768–1023px | Sidebar collapses to bottom nav or icon rail, 2-col grid |
| Mobile | <768px | Single column, stacked layout, hamburger menu |

- Touch targets: minimum 40×40px.
- Font sizes don't scale down below `--text-xs` (12px).
- Cards stack vertically on mobile; grids become single-column.
- Sidebar transforms to slide-out drawer on tablet/mobile.

---

## 9 · Agent Prompt Guide

Quick color reference for in-the-moment prompting:

> "StudyMate AI uses a warm Light Academic palette: cream `#faf9f7` backgrounds, white cards `#ffffff`, indigo `#6366f1` primary accent, teal `#14b8a6` secondary, near-black `#1a1c20` text. Fonts are Inter for body and Outfit for headlines. Cards have 10px radius and 1–2px soft shadows. No glassmorphism — depth comes from subtle shadow layers on flat surfaces."

Key constraints to remember:
- Warm cream, NOT cold gray
- One primary accent (indigo), one secondary (teal)
- Flat cards with soft shadows
- 10px radii for interactive elements
- Inter + Outfit font pairing
