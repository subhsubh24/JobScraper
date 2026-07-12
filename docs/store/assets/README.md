# Store assets (rendered, committed)

Real, committed store-listing image files. Every asset here is generated from a reviewable
source (HTML/CSS built on the real brand tokens — [BRAND_KIT](../../brand/BRAND_KIT.md)) so it is
never a hand-edited binary blob, and it is regenerable via a committed script.

## `feature-graphic.png` — Google Play feature graphic

- **Spec:** 1024 × 500 px, 24-bit PNG, **no alpha** (Play requires a feature graphic to publish).
- **Source:** [`scripts/store/feature_graphic.html`](../../../scripts/store/feature_graphic.html)
- **Regenerate:** `bash scripts/store/render_feature_graphic.sh` (needs a headless Chromium; see the
  script header). The script fails loud if the output isn't exactly 1024 × 500.
- **Design:** dark canvas (`#0B1020`), single restrained indigo accent (`#6366F1`), the "Career
  Operator" wordmark + chevron mark, the promise line *"Run your job search like an operator."*, a
  real fit-score signifier (`82` on the real ≥75 = green scale), and four real feature chips
  (fit score, mock interviews, tailored résumé, pipeline CRM). No stock imagery, no invented
  metric, no decorative gradient noise — it clears the VISION DESIGNER QUESTION.

### Accessible description / alt text (2026 Play a11y requirement)

> Career Operator — dark product banner. Top-left: the Career Operator wordmark beside its indigo
> chevron app mark. Top-right: a job-fit score badge reading "82 FIT" in green. Center headline:
> "Run your job search like an operator." Below it: "Fit scoring, role-specific interview prep, and
> an AI coach — over one pipeline," followed by four feature chips: Fit score & why · Mock
> interviews · Tailored résumé · Pipeline CRM.

## Not yet produced (honest status)

- **App screenshots** (iOS App Store + Google Play): require a **signed native build** of the Expo
  app captured on a real device/simulator — not producible on the Linux factory host. Tracked in
  [`ACCEPTANCE_AUDIT.md`](../ACCEPTANCE_AUDIT.md) A3/G7 and PENDING_OPS. Web-app captures are **not**
  substituted here — a native store listing must show the native app (honesty).
- **App icon:** `mobile/assets/images/icon.png` is still the Expo template; a bespoke brand mark is
  owner/designer work (a programmatically generated icon would read as generic-AI slop and fails the
  DESIGNER QUESTION — see BRAND_KIT). The feature graphic above is a typographic brand *banner* built
  from the design system, a different artifact class from a bespoke illustrative icon.
