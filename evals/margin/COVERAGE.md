# Margin eval coverage — JobScraper AI workflows

The frontier map for Margin's cost-per-outcome. Every AI workflow in the repo is enumerated with
its metered path, its real outcome signal, whether it has a Margin eval suite yet, and a rough
spend/importance rank so the coverage engine can prioritize the uncovered ones.

**Cost is already metered for all chat workflows** — every one routes through
`resilient_chat_completion` (`src/llm.py:138`), which emits a `record_call` with real tokens/latency
via `_emit_call_metrics` (`src/llm.py:27`). What an eval suite adds is the **graded OUTCOME** over a
representative input matrix, so cost-per-outcome is statistical, not anecdotal.

Legend — evaled?: ✅ suite shipped · 🟡 built this pass · ⬜ frontier (next).

| workflow | what it does | metered path (`file:line`) | real outcome signal | evaled? | spend/importance |
| --- | --- | --- | --- | --- | --- |
| **fit-scoring** | Ranks a job vs a résumé (semantic + skills). | embeddings `src/ranking/scorer.py:65`; outcome `scorer.py:217` | `JobScore.overall_score` 0–100 (deterministic heuristic OR embeddings) | ✅ `fit_scoring_cases.jsonl` (band grader, calibrated) | HIGH — runs on every job add |
| **mock-interview-scoring** | Scores one interview answer (relevance/specificity/STAR). | `src/enrichment/llm_workflows.py:642` → `src/llm.py:138` | `overall` 0–100 computed server-side from 3 sub-scores — a genuine numeric signal | 🟡 `mock_interview_scoring_cases.jsonl` (bimodal band grader) | HIGH — one paid call per answer, many per session |
| **cover-letter** | Generates a grounded cover letter for a job. | `src/enrichment/llm_workflows.py:321` → `src/llm.py:138` | usable, grounded letter: mentions company, references a JD skill, right length, no placeholder | 🟡 `cover_letter_cases.jsonl` (structural grader) | MED-HIGH — large output, paid feature |
| **coach-chat** | Conversational career coach (Premium). | `src/ai_coach/career_coach.py:152` → `src/llm.py:138` | on-topic, non-empty, grounded reply | ⬜ frontier | HIGH — interactive, many turns/user |
| **prep-pack** | Full interview prep pack (markdown sections). | `src/enrichment/llm_workflows.py:125` → `src/llm.py:138` | all required sections present + grounded in JD/résumé | ⬜ frontier | HIGH — largest single output; charges a usage |
| **parse-job-description** | Extracts structured fields from a JD (JSON). | `src/enrichment/llm_workflows.py:216` → `src/llm.py:138` | required fields present + valid (skills list, `remote_policy` ∈ enum) | ⬜ frontier | MED — small, but frequent |
| **mock-interview-question-gen** | Generates N role-specific questions (JSON). | `src/enrichment/llm_workflows.py:567` → `src/llm.py:138` | N valid `{question, category∈{technical,behavioral}}`, grounded | ⬜ frontier | MED — one call per session |
| **tailored-résumé** | Rewrites a résumé for a specific job. | `src/enrichment/llm_workflows.py:356` → `src/llm.py:138` | grounded rewrite: no fabricated experience, references JD | ⬜ frontier | MED |
| **study-plan** | N-day study plan for a role. | `src/enrichment/llm_workflows.py:288` → `src/llm.py:138` | structured plan covering JD skill gaps | ⬜ frontier | MED |
| **learning-plan** | Skill-gap learning plan. | `src/enrichment/llm_workflows.py:418` → `src/llm.py:138` | plan addresses the supplied top skill gaps | ⬜ frontier | MED |
| **salary-negotiation** | Negotiation script vs a target salary (Career+). | `src/enrichment/llm_workflows.py:465` → `src/llm.py:138` | script references the role + target number, actionable | ⬜ frontier | LOW-MED |
| **artifact-refinement** | Maker≠checker review pass over a drafted artifact. | `src/enrichment/llm_workflows.py:178` → `src/llm.py:138` | improved-not-degraded draft (fail-safe to draft) | ⬜ frontier (best evaled as a delta on its parent artifact) | LOW — secondary call |

## Covered this frontier pass

- **fit-scoring** — 60 cases + edge/fuzz; deterministic band grader, CI-calibrated (key-free).
- **mock-interview-scoring** — the flagship LLM workflow with a genuine *numeric* outcome. Bimodal
  grader: strong answers must score high, weak/blank/off-topic answers must score low. Its scoring
  code deliberately floors vague/empty answers, so the grader genuinely discriminates.
- **cover-letter** — a genuine *structural* success signal (grounding + completeness + no
  placeholder), so a degraded generator (template/placeholder/empty) fails.

## Why the rest are the frontier (honest)

The uncovered workflows are **LLM-only** (no deterministic key-free path), so a suite for each is
inherently on-demand/live and needs a real grader. They are ranked above by spend/importance:
**coach-chat** and **prep-pack** are the highest-value next targets. The coverage engine should walk
this table top-down. This pass deliberately did NOT boil the ocean — it enumerated everything and
shipped genuine graders for the top numeric + top structural workflows.

## Grading philosophy (same bar as fit-scoring)

- **Genuine signal, never always-pass.** Each grader can fail a bad output (a constant/blank/placeholder
  result fails). Verified in `tests/evals/test_margin_eval_suite.py` with synthetic inputs, no network.
- **LLM-only suites are skipped in the keyless run** (and in CI); they run on demand / on merge with a
  `GEMINI_API_KEY`. CI validates their *matrix + grader logic*, not a live call.
- **Cost is real.** For chat workflows the runner re-tags the app's `record_call` to the correct
  `workflow_id` + eval `session_id`, so emitted cost is the true paid path.
