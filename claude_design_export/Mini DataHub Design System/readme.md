# Mini DataHub Design System

A design system for **Mini DataHub (迷你 DataHub)** — a federated data portal for
embodied-AI / robot-manipulation training datasets. It unifies datasets from
heterogeneous sources (LeRobot/HuggingFace, Open X-Embodiment/RLDS, local
HDF5, rosbag/MCAP) behind one searchable catalog with quality scoring,
license-aware filtering, and a taxonomy-alignment engine for cross-source
task/scene/embodiment search.

This system was built from the **Huhrz/mini-datahub** GitHub repository
(https://github.com/Huhrz/mini-datahub) — specifically its Python catalog
backend (`schema.py`, `taxonomy.py`, `hub_data.py`, `quality.py`) and its
React + Tailwind web frontend (`web/src/App.jsx`, `web/src/CoverageHeatmap.jsx`).
**Explore that repo directly** for the full ingestion pipeline, source
adapters (`sources.py`), and quality-scoring engine (`quality.py`) — this
design system only recreates the front-of-house product surface, not the
data pipeline.

The source app was a functional prototype (Streamlit + a small React/Tailwind
UI) rather than a fully art-directed product. Per the brief, this system
**redesigns it into a more polished, professional data-platform aesthetic**
(in the spirit of Linear / Vercel / Hugging Face's restrained UI) while
preserving every real screen, filter, and data field from the source code.

## What the product does

- **Top banner** — product name + a one-line description of the four core
  capabilities (unify formats, catalog search, auto quality-check, coverage map).
- **3 stat cards** — dataset count / episode ("轨迹") count / frame count.
- **Dataset list** — card grid: name, id, quality score, and tags for
  embodiment, source format, commercial-use flag, episode count, failure labels.
- **Filter sidebar** — search, task-concept, embodiment, source format,
  provenance (采集方式), commercial-only toggle, failure-only toggle, min
  quality-score slider.
- **Detail drawer** — slides in from the right on card click: stat mini-cards,
  license/format/provenance/quality text, non-commercial warning, action
  convention tags, task/scene/modality tags, and links to the LeRobot
  dataset visualizer + the dataset's homepage.
- **Coverage map tab** — embodiment × task-concept heatmap; darker cell =
  more datasets, light gray = a coverage gap.

## Components

Location: `components/<group>/`. Every component's directory ships a
`<Name>.jsx` + `<Name>.d.ts` + `<Name>.prompt.md` + one `@dsCard` HTML.

- **forms/** — `Button`, `SearchInput`, `Select`, `Checkbox`, `Slider`
- **navigation/** — `Tabs`
- **data-display/** — `Tag`, `StatCard`, `DatasetCard`, `CoverageHeatmap`
- **feedback/** — `Alert`
- **overlay/** — `DetailDrawer`

This inventory is 1:1 with the UI vocabulary actually used in
`web/src/App.jsx` / `CoverageHeatmap.jsx` — no components were invented
beyond what the source screens needed.

**Intentional additions:** none. Every component above has a direct
counterpart in the source app (e.g. `Tag` = the source's inline `Tag`
component with its `TONES` map; `Alert` = the inline amber warning box in
`Detail`).

## UI kit

`ui_kits/data-hub/` — an interactive, click-through recreation of the full
product: header, stat cards, tabs, filter sidebar (all filters functional
against mock data), dataset cards, detail drawer, and the coverage heatmap.
Mock data (`mock-data.js`) mirrors `schema.py`'s `DatasetMeta` fields exactly.

## Index / manifest

- `readme.md` — this file
- `SKILL.md` — Claude Code / Agent Skill packaging
- `styles.css` — root stylesheet (imports only)
- `tokens/` — `colors.css`, `typography.css`, `spacing.css`, `fonts.css`, `base.css`
- `guidelines/colors/` — neutral, accent, tag-tone, surface specimen cards
- `guidelines/type/` — type scale, monospace/data-value specimen cards
- `guidelines/spacing/` — spacing scale, radius scale, shadow scale
- `guidelines/brand/` — wordmark card (no real logo in source, see below)
- `components/` — 12 components across 5 groups (see above)
- `ui_kits/data-hub/` — the full interactive product recreation

## Content fundamentals

The source app's copy is **all Simplified Chinese**, written in a plain,
technical, documentation-like voice — closer to an engineering README than
consumer marketing copy. Carried into this system:

- **Register**: neutral/technical, third-person-ish — never addresses the
  user as "你" in the UI chrome itself (labels are nouns: "筛选" not "开始筛选
  吧"). The one exception is the warning banner, which does address the
  user directly with an imperative: `请勿混入商业训练集` ("do not mix into
  commercial training data").
- **Casing/punctuation**: no exclamation points, no marketing superlatives.
  Chinese full-width punctuation (`·` as a separator, `—— ` as an em-dash
  lead-in) e.g. `跨源聚合 · 统一检索 · 自动质检 · 覆盖度地图 —— 具身智能数据的联邦门户`.
  This dot-separated capability list is a reusable pattern for subheadlines.
  Section labels are short 2–4 character nouns: `筛选` (Filter), `任务概念`
  (Task concept), `本体类型` (Embodiment type), `质量分` (Quality score).
- **Emoji**: used sparingly as *functional glyphs*, not decoration — 🤖
  (robot, in the H1), 🔎 (filter section), 🎬 (play/visualize action), 🔗
  (external link), ⚠️ (warning). This system upgrades those to a real icon
  set (Lucide) instead of removing them — see Iconography below.
- **Numbers over adjectives**: the product leads with counts and scores
  (`128` datasets, `质量 0.91`) rather than descriptive language — a data-hub
  should let the numbers do the talking.
- **Vibe**: internal tool / research-infra energy — built by and for ML
  engineers evaluating training data, not a public marketing site. Keep
  copy terse, keep every filter label a literal field name.

## Visual foundations (v2 — "更高级感" pass)

Revised per direct request to feel more premium, referencing Humaid's dark,
confident nav/hero treatment — without copying its pure black/white palette.

- **Color**: accent moved from indigo to a **teal/cyan** ramp (`#06b6d4`
  family) for a more "科技感" read. Neutrals stayed zinc/gray. **Dual
  theme**: every semantic surface/text/border/tone alias has a
  `[data-theme="dark"]` override — light is the default, dark repoints to
  near-black surfaces (`gray-950/900/850`) with a brighter accent
  (`accent-400`) for contrast. Base scales (`--gray-*`, `--accent-*`) are
  fixed; only the semantic layer switches. The header/emphasis panel
  (`--surface-inverse`) is intentionally **not** themed — it stays a
  constant near-black bar in both light and dark, matching the
  reference's always-dark nav rather than flipping to white on dark pages.
  Semantic tag tones (slate/teal/emerald/amber/rose) keep their emerald/
  amber/rose hues from the source's `TONES` map, only the accent tone
  shifted with the rest of the palette.
- **Type**: source used a system-font stack with no custom webfont (see
  Font substitution below). UI/display type is now **Space Grotesk** — a
  wide, geometric grotesk that reads confidently at hero sizes (uppercase
  + `--tracking-hero` letter-spacing on H1/wordmark, echoing the
  reference's wide-tracked all-caps title). Display scale grew 32→40px to
  give the hero more presence. Data values (ids, SPDX license strings,
  quality scores) stay in **IBM Plex Mono**, unchanged, to read as literal
  data — mirroring the source's `<code>` treatment of `license_spdx` /
  `source_format`.
- **Spacing**: 4px-based scale (4/8/12/16/20/24/32/40/48/64).
- **Backgrounds**: flat only — no photography, no illustration, no texture,
  no gradients (the one gradient in the source, the header banner, is
  intentionally removed). Page background is a very light gray
  (`var(--surface-page)`), cards are white.
- **Animation**: none beyond simple property transitions — the source uses
  plain CSS `transition` on hover states only (button/card hover, tab
  active state), no entrance animation, no bounce/spring easing. This
  system keeps that: a single `--ease-standard` cubic-bezier, 120–260ms.
- **Hover states**: cards lift with a slightly stronger shadow and an
  accent-tinted border (`hover:shadow-md hover:border-brand-500` in the
  source); buttons darken one step (`hover:bg-brand-700`).
- **Press states**: not explicitly defined in the source; kept simple
  (browser default) rather than inventing a new pattern.
- **Borders**: 1px, `--border-subtle` (very light gray) on cards,
  `--border-default` on form inputs — thin and quiet throughout, never a
  colored accent border.
- **Shadows**: `shadow-sm` at rest on all cards, `shadow-md` on hover,
  `shadow-2xl` on the slide-over drawer only. No inner shadows.
- **Corner radii**: exact source values — `6px` (badges/inputs),
  `8px` (cards, buttons), `12px` (sidebar/heatmap panel), `16px` (drawer-
  scale containers), full-pill for nothing in particular (reserved token,
  unused by the source's actual UI).
- **Cards**: white surface, 1px light-gray border, `shadow-sm`, 8–12px
  radius — no colored left-border accent (explicitly avoided per brief).
- **Transparency/blur**: the only translucent surface is the drawer's
  backdrop scrim (`black/30`no blur) — no frosted-glass/backdrop-blur
  anywhere in the source.
- **Layout**: fixed max-width content column (source: `max-w-7xl`≈1280px),
  fixed-width sidebar (256px source → 264px token), everything else fluid.
- **Imagery**: none — this is a metadata/text product with no photography
  or illustration in the source; no imagery was invented for this system.

## Iconography

The source app uses **emoji as its entire icon system** — 🤖 🔎 🎬 🔗 ⚠️ —
no icon font, no SVG sprite, no PNG icon set. There is nothing to copy in.

**Substitution flagged:** this system replaces those emoji with
**Lucide** (https://lucide.dev), loaded from CDN
(`https://unpkg.com/lucide@latest`), because the brief calls for a more
"professional data platform" look and hand-rolled/emoji icons read as
prototype-grade. Lucide was chosen for its neutral, uniform 2px stroke
weight that matches the rest of the system's restrained, non-decorative
aesthetic. Mapping used: 🤖→(dropped, wordmark only) · 🔎→`sliders-horizontal`
· 🎬→`play` · 🔗→`external-link` · ⚠️→`alert-triangle` · plus `database`,
`git-branch`, `film` for the three stat cards (not present in source, added
only as stat-card affordances, easily removed). **If real product icons
exist elsewhere in the org, swap this substitution out.**

## Brand / logo

**No logo was found anywhere in the source repository** (no image assets,
no favicon beyond default, no SVG mark). Per instructions, **no logo was
invented**. The wordmark "Mini DataHub" is set in plain type wherever a
mark would normally go (see `guidelines/brand/wordmark.card.html`). If the
org has a real mark, add it to `assets/` and update the header component.

## Font substitution — please read

The source repository has **no font files and no `@font-face` rule** — the
web app uses a plain system-font stack
(`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC",
"Microsoft YaHei", sans-serif`). This system substitutes **Space Grotesk**
(UI/display) + **IBM Plex Mono** (ids/values), loaded from Google Fonts —
a wide geometric grotesk paired with a technical mono, chosen for a more
premium/confident feel (ref. Humaid's hero treatment) while staying
data-tool-appropriate. **This is a flagged substitution, not a real brand
font.** If the organization has a real typeface, please supply the font
files (or a Google Fonts / Adobe Fonts name) and this system will be
updated to use it.

## Sources

- GitHub: https://github.com/Huhrz/mini-datahub — read `README.md`,
  `schema.py`, `taxonomy.py`, `hub_data.py`, `quality.py`, `app.py` (the
  Streamlit prototype) and `web/src/App.jsx` + `web/src/CoverageHeatmap.jsx`
  (the React/Tailwind web frontend) to go deeper than this design system
  does — e.g. to see the real source-adapter framework (`sources.py`), the
  taxonomy alignment engine, and the DuckDB-backed catalog queries.

## Caveats

- No real brand assets (logo, fonts, product photography) were provided —
  see the flagged substitutions above. Please attach real ones if/when
  available.
- The visual direction (flat indigo accent, no gradient, IBM Plex pairing)
  is one professional interpretation of "modern/clean/tech-forward" — happy
  to explore alternate palettes/type pairings as tweaks.
- Component set is scoped to what `App.jsx`/`CoverageHeatmap.jsx` actually
  use; if the real product has more screens (ingestion flows, admin views,
  the Streamlit `app.py` surface) not reflected here, point me at them and
  I'll extend the kit.
