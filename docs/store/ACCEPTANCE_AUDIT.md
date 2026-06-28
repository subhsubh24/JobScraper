# STORE ACCEPTANCE AUDIT — Apple App Store + Google Play

> Self-audit vs the **CURRENT** Apple App Store Review Guidelines and Google Play
> Developer Program Policies. Status legend: **FAIL** (will be rejected / not built),
> **OPEN** (not yet verified), **PASS** (verified artifact on default branch).
> Readiness requires **ZERO open FAILs**. At the readiness gate, RE-FETCH the live
> guidelines via web research (they change) and re-verify every row against a real build.
>
> Updated 2026-06-28: reconciled to shipped artifacts. Account deletion, hosted privacy
> policy/ToS, web subscription billing, and the privacy-labels/data-safety/permissions
> drafts now exist; rendered store assets and the mobile (StoreKit/Play Billing) purchase
> flow do **not**, so submission readiness remains **NO** (honest).

## Apple — App Store Review Guidelines

| # | Guideline area | Requirement | Status | Notes |
|---|---|---|---|---|
| A1 | 1.x Safety | No objectionable content; UGC/AI output moderated | PARTIAL | AI coach now has a content-safety guardrail on input + output (self-harm→crisis resources, violence/hate/sexual-gen blocked; conservative so legit career topics pass) + hardened system prompt — `src/ai_coach/moderation.py`, 35 tests (PR #51). REMAINING (follow-ups, not blocking build): a user-facing "report this response" affordance, and the same output filter on the prep-pack generators (`src/enrichment/llm_workflows.py`). |
| A2 | 2.1 App Completeness | No crashes, no placeholder content, all features work | OPEN | Backend journeys pass at runtime; full native completeness pending a signed device build (CI/Human) |
| A3 | 2.3 Accurate Metadata | Screenshots/description match real app | FAIL | ASO copy drafted (`ASO_COPY.md`); rendered screenshots/feature graphic need a running build — not yet produced |
| A4 | 3.1.1 In-App Purchase | Digital subscriptions via StoreKit, not external payment | FAIL | Web Stripe billing built (PR #40); **mobile** StoreKit/RevenueCat NOT integrated — required before iOS submission |
| A5 | 3.1.2 Subscriptions | Clear terms, price, period, restore purchases | OPEN | Terms drafted (`ASO_COPY.md` disclosure); restore-purchases requires the StoreKit integration (A4) |
| A6 | 4.0 Design | Polished, native, not a web wrapper | OPEN | Native Expo app built to the design bar; final review at the gate vs a real build |
| A7 | 5.1.1 Privacy / Data Collection | Privacy policy + App Privacy labels accurate | OPEN | Privacy policy hosted + linked (PR #38) PASS; App Privacy labels drafted (`APP_PRIVACY_LABELS.md`) — owner enters them in App Store Connect + counsel review |
| A8 | 5.1.1(v) Account Deletion | In-app account deletion required | PASS | `DELETE /api/auth/me` cascade-deletes all user data (PR #36); mobile Settings "Delete account" calls it |
| A9 | 5.1.2 Data Use | Permission strings for any data accessed | PASS | Zero sensitive permissions used; audited in `PERMISSIONS_AUDIT.md` — nothing to justify |
| A10 | 5.6 Developer Code of Conduct | No fake reviews / ratings manipulation | OPEN | Growth boundary enforces this; nothing published yet |

## Google — Play Developer Program Policies

| # | Policy area | Requirement | Status | Notes |
|---|---|---|---|---|
| G1 | Data Safety form | Accurate data-collection disclosure | OPEN | Content drafted (`APP_PRIVACY_LABELS.md` → Data Safety section); owner enters it in Play Console |
| G2 | User Data policy | Privacy policy linked + in-app | PASS | `/privacy` + `/terms` hosted + linked (PR #38) |
| G3 | Account deletion | In-app + web account/data deletion path | PASS | Same `DELETE /api/auth/me` cascade (PR #36) |
| G4 | Subscriptions / Play Billing | Digital goods via Play Billing | FAIL | Web Stripe built (PR #40); **Play Billing** NOT integrated — required before Android submission |
| G5 | Permissions | Request only necessary permissions + rationale | PASS | Zero dangerous permissions; audited in `PERMISSIONS_AUDIT.md` |
| G6 | Broken functionality | App must work as described | OPEN | Backend journeys pass; native end-to-end pending a build (CI/Human) |
| G7 | Store listing assets | Icon, feature graphic, screenshots (real files) | FAIL | App icon exists; feature graphic + screenshots need a running build — not yet produced |
| G8 | Deceptive behavior | No misleading claims / fake metrics | OPEN | Honesty standard enforced; copy is truthful to current features |

## Cross-cutting blockers (must be PASS before submission)
- [x] Privacy policy + ToS hosted and linked (A7, G2) — PR #38
- [x] In-app account deletion (A8, G3) — PR #36
- [x] App Privacy labels / Data Safety form content drafted + accurate (A7, G1) — this audit
- [x] Permissions minimized + audited (A9, G5) — `PERMISSIONS_AUDIT.md`
- [ ] Mobile subscription purchase flow w/ restore (A4–A5, G4) — StoreKit/Play Billing not built
- [ ] All core flows verified at runtime on a real build (A2, G6) — needs signed build (CI/Human)
- [ ] Rendered, accurate store assets committed (A3, G7) — needs a running build
- [x] AI-output safety guardrail (A1) — coach input+output moderation shipped (PR #51);
      follow-ups: user-facing report affordance + prep-pack generator output filter
- [ ] Owner enters App Privacy / Data Safety answers in the consoles + counsel review (PENDING_OPS)

**Open FAILs remain (mobile billing, rendered assets). Submission readiness: NO.**
Re-audit vs live guidelines at the gate.
