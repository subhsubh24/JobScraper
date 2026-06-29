# App Privacy Labels + Google Data Safety — Career Operator

> **Code-accurate disclosure** of exactly what the app collects, why, and who receives it.
> Source of truth: the SQLAlchemy models (`src/db/models.py`), the LLM call sites
> (`src/ranking/scorer.py`, `src/enrichment/llm_workflows.py`, `src/ai_coach/career_coach.py`),
> and the hosted Privacy Policy (`web/app/privacy/page.tsx`). Keep this in sync with the
> code; re-verify at the readiness gate. Auto-authored — counsel review is an owner action
> (PENDING_OPS: `legal-review`).

## What the app actually collects (from the data model)

| Data | Where | Purpose | Linked to the user? |
|---|---|---|---|
| Email address | `users.email` | Account creation + sign-in | Yes |
| Name (optional) | `users.full_name` | Personalization | Yes |
| Resume text (optional) | `users.resume_text` | Fit scoring + AI prep/coach context | Yes |
| Resume/JD embeddings | `users.resume_embedding`, `job_postings.jd_embedding` | Similarity scoring (derived from the above) | Yes |
| Saved jobs + applications | `job_postings`, `applications` | The core pipeline CRM | Yes |
| AI coach chat history | `chat_messages` | Conversation continuity | Yes |
| Prep artifacts | `prep_artifacts` | Generated interview prep the user keeps | Yes |
| Usage counters | `users.jobs_added_this_month`, `prep_packs_this_month` | Free-tier limit enforcement | Yes |
| Subscription status | `subscriptions` (Stripe customer/subscription id, plan, status) | Entitlement / billing state | Yes |
| Server request logs (IP, timestamp, path) | Hosting provider (Vercel) | Security, rate-limiting, operations | Not used to build a profile |

**Password** is stored only as a salted PBKDF2 hash (`users.password_hash`) — never in
plaintext, never transmitted to third parties.

> The data model also contains `contacts` / `outreach_sequences` tables (a planned
> networking/outreach CRM). There is **no shipped user path to populate them yet**, so the
> app does not currently collect that data — add it to this disclosure (user-entered
> business contact info) the moment the outreach feature ships.

## What the app does NOT collect
Location, precise or coarse · Photos / camera / microphone · Contacts · Calendar · Health
or fitness · Browsing/search history outside the app · Advertising identifiers (IDFA/GAID)
· Device fingerprinting · Any cross-app/cross-site tracking. **No data is sold. No data is
used for third-party advertising. No tracking SDKs are present.**

## Third parties that receive data (service providers only)

| Recipient | Data sent | When | Role |
|---|---|---|---|
| Google Gemini (LLM/embeddings) | Resume text, job descriptions, and coach messages | Only when the user runs scoring / generates prep / chats with the coach | Processing on our behalf |
| Neon (Postgres) | All stored rows above | At rest | Data storage |
| Vercel | HTTP request metadata (logs) | Every request | Hosting |
| Stripe | Name/email + card details entered on Stripe Checkout (we never see the card) | At subscription purchase (when billing is live) | Payment processing |

These are **service providers processing data on our behalf**, not independent data sales.

---

## Apple — App Privacy (App Store Connect "App Privacy" questionnaire)

**Data Used to Track You:** **None.**

**Data Linked to You** (collected and tied to identity, used for *App Functionality* only —
not Tracking, not Third-Party Advertising):
- **Contact Info** → Email Address; Name (optional)
- **User Content** → Other User Content (resume text, saved job descriptions, AI coach
  messages, generated prep artifacts)
- **Identifiers** → User ID
- **Purchases** → Purchase History (subscription plan/status) — *applies once billing is live*
- **Usage Data** → Other Usage Data (free-tier counters: jobs added / prep packs generated
  this month — used solely for entitlement enforcement, not analytics or tracking)

**Data Not Linked to You:**
- **Diagnostics** → Other Diagnostic Data (server request logs: IP + timestamp, retained
  short-term for security/operations; not used to identify or profile users)

All other Apple categories (Health & Fitness, Financial Info beyond the above, Location,
Sensitive Info, Contacts, Browsing History, Search History, Usage Data for tracking): **Not
Collected.**

---

## Google — Play Data Safety form

**Does your app collect or share user data?** Yes (collect). **Sharing** (transfer to
independent third parties): No — data goes only to service providers processing on our
behalf, which Google classifies as collection-with-processing, not sharing/selling.

**Data types collected:**
- **Personal info** → Email address; Name (optional); **User IDs** (the account identifier)
- **Financial info** → Purchase history (subscription status) — *once billing is live*
- **App activity** → Other user-generated content (resume, saved jobs/applications, coach
  messages, prep artifacts)
- **App info & performance** → **Diagnostics** only (server-side request logs: IP +
  timestamp). No crash-reporting SDK is present, so "Crash logs" is NOT collected.

(The account User ID is a server-side identifier under *Personal info → User IDs* — NOT a
device/advertising ID, so "Device or other IDs" is **not** collected.)

**Security practices:**
- Data is **encrypted in transit** (HTTPS/TLS everywhere; HSTS enforced).
- Data is **encrypted at rest** (Neon managed Postgres encrypts at rest by default).
- Users can **request that data be deleted** — in-app **Delete account** (`DELETE
  /api/auth/me`) cascade-removes all user-owned rows.
- Passwords are stored hashed (PBKDF2-HMAC-SHA256, per-user salt), never plaintext.
- **No data sold.** **No data shared for advertising.** No advertising/analytics tracking SDKs.

**Account/data deletion URL + in-app path:** in-app Settings → Delete account; web Privacy
Policy documents the deletion path. (Owner action: confirm the public deletion-request URL
in the Play listing.)

### Data retention (code-accurate)
Both consoles' privacy reviews — and the Privacy Policy — should state how long data is kept.
The honest, code-backed answer:
- **Account-linked data** (email, optional name, resume text, saved jobs/applications, coach
  messages, prep artifacts, subscription status): retained **only while the account exists**.
  There is **no soft-delete and no post-deletion retention window** in the app — `DELETE
  /api/auth/me` cascade-removes every user-owned row immediately (proven by
  `tests/test_account_and_security.py`: zero rows across all user-owned tables after deletion).
- **Operational diagnostics** (server request logs: IP + timestamp): retained per the hosting
  platform's default log-retention window, not in the application DB. **Owner action:** set an
  explicit log-retention cap on the platform and record the number here (do not invent one).
- **HONEST CAVEAT — backups:** if the owner enables point-in-time recovery / DB backups (a
  recoverability net the auto-migrate runbook recommends), deleted rows may persist in those
  backups until the backup window rolls off. This is standard and must be disclosed: live data
  is deleted immediately, but a backup copy expires on the provider's backup schedule. The
  Privacy Policy should state the backup-retention window once the owner sets it.

---

## Open items (owner / not buildable in-repo)
- Counsel review of this disclosure + the Privacy Policy (PENDING_OPS: `legal-review`).
- Enter these answers into App Store Connect (App Privacy) and Play Console (Data Safety)
  at submission — these forms live in the consoles, not the repo.
- Re-verify against the data model at the readiness gate (a new collected field = a new row
  here).
