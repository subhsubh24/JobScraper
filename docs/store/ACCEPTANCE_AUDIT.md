# STORE ACCEPTANCE AUDIT — Apple App Store + Google Play

> Self-audit vs the **CURRENT** Apple App Store Review Guidelines and Google Play
> Developer Program Policies. Status legend: **FAIL** (will be rejected / not built),
> **OPEN** (not yet verified), **PASS** (verified artifact on default branch).
> Readiness requires **ZERO open FAILs**. At the readiness gate, RE-FETCH the live
> guidelines via web research (they change) and re-verify every row against a real build.
>
> As of bootstrap (2026-06-27): the mobile app is being scaffolded; nothing is
> submission-verified. Everything is **FAIL/OPEN** — honestly.

## Apple — App Store Review Guidelines

| # | Guideline area | Requirement | Status | Notes |
|---|---|---|---|---|
| A1 | 1.x Safety | No objectionable content; user-generated content moderated | OPEN | AI coach output needs safety guardrails |
| A2 | 2.1 App Completeness | No crashes, no placeholder content, all features work | FAIL | Backend endpoints are build-but-broken |
| A3 | 2.3 Accurate Metadata | Screenshots/description match real app | FAIL | No rendered store assets yet |
| A4 | 3.1.1 In-App Purchase | Digital subscriptions via StoreKit, not external payment | OPEN | RevenueCat/StoreKit not integrated |
| A5 | 3.1.2 Subscriptions | Clear terms, price, period, restore purchases | OPEN | Paywall not built |
| A6 | 4.0 Design | Polished, native, not a web wrapper | OPEN | Expo app being built to design bar |
| A7 | 5.1.1 Privacy / Data Collection | Privacy policy + App Privacy labels accurate | FAIL | No privacy policy / labels yet |
| A8 | 5.1.1(v) Account Deletion | In-app account deletion required | FAIL | Not implemented |
| A9 | 5.1.2 Data Use | Permission strings for any data accessed | OPEN | Only request what we use |
| A10 | 5.6 Developer Code of Conduct | No fake reviews / ratings manipulation | OPEN | Growth boundary enforces this |

## Google — Play Developer Program Policies

| # | Policy area | Requirement | Status | Notes |
|---|---|---|---|---|
| G1 | Data Safety form | Accurate data-collection disclosure | FAIL | Not drafted |
| G2 | User Data policy | Privacy policy linked + in-app | FAIL | No privacy policy yet |
| G3 | Account deletion | In-app + web account/data deletion path | FAIL | Not implemented |
| G4 | Subscriptions / Play Billing | Digital goods via Play Billing | OPEN | Not integrated |
| G5 | Permissions | Request only necessary permissions + rationale | OPEN | Minimize permissions |
| G6 | Broken functionality | App must work as described | FAIL | Backend build-but-broken |
| G7 | Store listing assets | Icon, feature graphic, screenshots (real files) | FAIL | Not rendered |
| G8 | Deceptive behavior | No misleading claims / fake metrics | OPEN | Honesty standard enforced |

## Cross-cutting blockers (must be PASS before submission)
- [ ] Privacy policy + ToS hosted and linked (A7, G2)
- [ ] In-app account deletion (A8, G3)
- [ ] Real subscription purchase flow w/ restore (A4–A5, G4)
- [ ] All core flows actually work at runtime (A2, G6)
- [ ] Rendered, accurate store assets committed (A3, G7)
- [ ] App Privacy labels / Data Safety form accurate (A7, G1)

**Open FAILs: many. Submission readiness: NO.** Re-audit vs live guidelines at the gate.
