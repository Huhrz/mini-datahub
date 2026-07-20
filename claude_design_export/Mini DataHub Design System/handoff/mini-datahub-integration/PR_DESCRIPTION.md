# Mini DataHub — visual refresh (design-system v2)

Applies the Mini DataHub Design System's v2 visual direction to the real
`web/` React frontend. No data/API/behavior changes — styling + one new
dependency only.

## What changed

1. **Accent color**: indigo (`brand-*`, `#4f46e5`) → teal/cyan (`accent-*`,
   `#06b6d4`). Applied everywhere `brand-*` classes were used (tabs, quality
   score, buttons, hover borders) and in the coverage heatmap's color ramp.
2. **Removed the gradient banner** — header is now a solid dark bar
   (`bg-zinc-900`), no `from-brand-600 via-violet-600 to-blue-600`.
3. **Dark mode** — Tailwind `darkMode: "class"`, toggled by a button in the
   header (defaults to light, persisted to `localStorage`). Every surface/
   text/border class got a `dark:` variant.
4. **Typography** — UI font swapped to **Space Grotesk** (wide, geometric —
   the header H1 is now uppercase with wide tracking); data values (ids,
   license, quality score) set in **IBM Plex Mono**. Both loaded via Google
   Fonts `@import` in `index.css`. *(Flagged substitution — swap for a real
   brand font if the org has one.)*
5. **Icons** — the emoji icon set (🤖 🔎 🎬 🔗 ⚠️) replaced with
   [lucide-react](https://lucide.dev) icons (`Search`, `SlidersHorizontal`,
   `Play`, `ExternalLink`, `AlertTriangle`, `Sun`/`Moon`).

## New dependency

```
npm install lucide-react
```

## Files touched (this folder mirrors the repo — copy over or `git apply`)

- `web/tailwind.config.js` — `darkMode`, `accent` color scale, font families
- `web/src/index.css` — Google Fonts import, dark-mode body background
- `web/src/App.jsx` — full file, `brand-*` → `accent-*`, dark: variants,
  lucide icons, theme toggle button + state
- `web/src/CoverageHeatmap.jsx` — full file, teal color ramp, dark-mode-
  aware empty-cell color

## How to apply

1. Copy these four files into your `web/` tree at the same relative paths
   (overwriting the originals), or diff them against your current versions
   if you've since changed something. **Note:** `App.jsx` and
   `CoverageHeatmap.jsx` are packaged here as `.jsx.txt` (so this design-
   system project doesn't try to compile them as its own components) —
   rename them back to `.jsx` when you copy them into your repo.
2. `npm install lucide-react` inside `web/`.
3. `npm run dev` and check both light and dark (toggle button, top right
   of the header).
4. Open a PR — suggested title: *"refresh: teal accent, dark mode, Space
   Grotesk, lucide icons (design-system v2)"*.

## Source

Design system: this project's `readme.md` / `guidelines/` /
`components/` — see especially `tokens/colors.css` (the `[data-theme=
"dark"]` semantic overrides these Tailwind `dark:` classes mirror) and
`ui_kits/data-hub/` (the standalone HTML reference this patch is based on).
