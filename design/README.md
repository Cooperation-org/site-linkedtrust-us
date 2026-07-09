# LinkedTrust design language — the shared core

This directory is the **canonical home** of the design language for the LinkedTrust
family of apps (the site, GovKit, amebo, demos, …).

| File | What it is |
|---|---|
| [`pattern-language.md`](pattern-language.md) | The language itself — 18 named patterns, Alexander-style, from surfaces and type down to buttons and page compositions. Read this before designing anything in the family. |
| [`tokens.css`](tokens.css) | The runnable core: one dependency-free stylesheet. Design tokens as CSS custom properties (light + dark, WCAG AA, the six validated leaf colors) plus the shared components (quiet buttons, ledger tables, leaves, badges, traces, bars). No fonts shipped, no JS, no animation — safe under a strict CSP and offline. |

## How an app adopts it

1. **Vendor `tokens.css`** into the app's static files (self-hostable apps must not
   hot-link; the family has no CDN). Note the source + sync date in a comment.
2. **Theme at the roots** (pattern 18): override the custom properties in a small
   app-level or org-level stylesheet loaded after it — accent, paper, even the leaf
   set. Never fork selectors to re-brand; if you're rewriting rules, the theme layer
   failed and that's a bug against the language.
3. **Changing a leaf color?** Re-validate the six-color set (both modes) with the
   dataviz palette validator before shipping — the current values pass CVD ΔE ≥ 12
   adjacent, ≥ 3:1 contrast, and the per-mode lightness band.
4. **Edits flow canonical-first**: change the language/tokens here, then sync vendored
   copies (currently: GovKit `static/govkit.css` + `docs/design/pattern-language.md`).

Class names carry a historical `gk-` prefix (the language was grown on GovKit, its
first reference implementation — live at https://demos.linkedtrust.us/govkit/). The
prefix is just a namespace; the tokens (`--gk-*`) are the API that themes touch.

## Where it came from

Grown 2026-07-08 from the LinkedTrust tree logo (dark plum trunk, six colored leaves)
and the hand-designed parts of linkedtrust.us, per Golda's brief: minimal, quiet,
human, organic — the content is the meat; small quiet buttons; the tree motif never
overdone; **never any animation**.
