# Margin cost-per-outcome eval suites — JobScraper AI workflows

These suites give [Margin](https://github.com/subhsubh24/Margin.ai) an **accurate, statistical**
cost-per-outcome for JobScraper's AI workflows — measured over representative input matrices, not
single hand-picked requests. See **`COVERAGE.md`** for the full frontier map of every AI workflow
in the repo (covered + uncovered, ranked by spend).

## What's here

| File | Role |
| --- | --- |
| `COVERAGE.md` | The frontier map: every AI workflow, its metered path, outcome signal, eval status, spend rank. |
| `fit_scoring_cases.jsonl` | 75 job+candidate pairs across the full fit spectrum (strong/partial/weak/mismatch) + edge/fuzz. Deterministic band grader. |
| `mock_interview_scoring_cases.jsonl` | 16 answers (strong vs weak/blank/off-topic) — the flagship LLM workflow with a real numeric score. Bimodal grader. |
| `cover_letter_cases.jsonl` | 8 job+résumé pairs — structural grader (grounded in company + a JD skill, right length, no placeholder). |
| `bands.json` | The fit-scoring expected-band → score-window table. |
| `../../scripts/margin_eval.py` | The runner (`--workflow {fit-scoring,mock-interview-scoring,cover-letter,all}`): runs each case through the REAL path, grades it, emits calls + graded outcomes via `margin-meter`. |
| `../../tests/evals/test_margin_eval_suite.py` | The keyless, network-free CI guard (integrity + calibration + grader-genuineness for all suites). |

## Workflows + graders

- **fit-scoring** (deterministic, key-free) — `JobScore.overall_score` band grader; CI-calibrated.
- **mock-interview-scoring** (LLM-only) — the server-computed answer score (relevance+specificity+STAR).
  Bimodal: strong answers must score high, weak/blank/off-topic low. The scorer deliberately floors
  vague/empty answers, so the grader genuinely discriminates.
- **cover-letter** (LLM-only) — structural success signal on the generated letter: mentions the
  company, references ≥1 JD skill, right length, no unfilled placeholder. A template/placeholder/empty
  generation fails.

LLM-only suites are **skipped without `GEMINI_API_KEY`** (and never run in the keyless CI gate); CI
validates their matrix + grader logic on synthetic inputs, no network. For chat workflows the runner
re-tags the app's in-request `record_call` to the correct `workflow_id` + eval `session_id`, so
emitted cost is the true paid path.

## The outcome + the grader (genuine, not always-pass)

The **outcome** is the real fit signal: `JobScore.overall_score` (0–100) from
`JobScorer.score_job`. Each case carries an **expected fit band**; the grader passes a case only
when its real score lands in that band's window (`bands.json`):

| band | window `[lo, hi)` |
| --- | --- |
| strong | `[62, 100]` |
| partial | `[48, 62)` |
| weak | `[38, 48)` |
| mismatch | `[0, 38)` |

The windows are **non-overlapping**, so the grader actually distinguishes fit quality: a degenerate
scorer that returned a constant 50 for every case would **fail all 15 strong and all 15 mismatch
cases**. That property is asserted in the CI test — the suite can't silently degrade into
always-pass.

Emitted outcome fields: `workflow_id="jobscraper-fit-scoring"`, `passed=<in-band>`,
`quality_score=<score/100>`, `quality_method="ground_truth"` (the score is graded against
each case's **labeled expected band** — Margin's honest provenance label), `session_id="eval:<run-id>"`.

## Modes

- **fit-scoring, heuristic (default, key-free).** `score_job` runs locally (semantic baseline 0.5,
  so `overall = 30 + 40·skills_score`) — **no LLM call, no AI cost** (honest zero-cost baseline).
  Deterministic, so the grader is fully **calibrated** and CI verifies every case lands in-band.
- **fit-scoring, embeddings (`--embeddings`, needs `GEMINI_API_KEY`).** Real Gemini embeddings for
  the semantic half; the runner meters each call (real tokens → real cost).
- **LLM-only workflows (mock-interview-scoring, cover-letter).** Require `GEMINI_API_KEY`; skipped
  cleanly without one. Cost is the true paid chat call (re-tagged to the workflow). Cost-capped by
  `--max-llm-cases` (default 40).

## How to run

```bash
# 1) Dry run — score + grade + print, emit nothing (no network). LLM suites report SKIPPED:
python scripts/margin_eval.py --dry-run

# 2) Emit fit-scoring to Margin (heuristic; zero AI cost baseline). SDK reads its env internally:
export MARGIN_INGEST_URL="https://<your-margin-deployment>"
export MARGIN_INGEST_KEY="mgk_..."          # per-project ingest key
python scripts/margin_eval.py --workflow fit-scoring

# 3) REAL metered cost-per-outcome across ALL workflows, cost-capped:
export GEMINI_API_KEY="..."
python scripts/margin_eval.py --workflow all --embeddings --max-llm-cases 30

# 4) One workflow, with a model override (e.g. compare models):
python scripts/margin_eval.py --workflow mock-interview-scoring --model gemini-2.5-flash --run-id compare-a
```

Batches are tagged `session_id="eval:<run-id>"` (calls) / `link="eval:<run-id>"` (outcomes) so eval
traffic is separable from production. The runner is **fail-safe**: missing SDK or
`MARGIN_INGEST_URL`/`MARGIN_INGEST_KEY` → telemetry disabled (still scores, grades, prints); missing
`GEMINI_API_KEY` → fit-scoring runs heuristic, LLM suites skip.

## CI policy

The runner is **on-demand / scheduled only** — it is **not** invoked by `scripts/preflight.sh ci`,
so the keyless CI gate makes **no** Gemini call and stays green. CI runs
`tests/evals/test_margin_eval_suite.py`, which validates suite integrity + heuristic calibration
with zero network. Wire the paid `--embeddings` run into a scheduled/manual workflow with the
`GEMINI_API_KEY` + `MARGIN_INGEST_*` secrets.

## Honest caveats / known gap

- **`bands.json` is calibrated for the heuristic path.** In embeddings mode the real semantic
  signal shifts absolute scores upward, and modern embedding models have a **similarity floor**
  (even unrelated professional text scores moderately similar), so a "clear mismatch" resume can
  still earn moderate semantic similarity. Grading an embeddings-mode run against these windows is
  therefore an **honest measurement** that includes that floor effect — not a fabricated
  always-pass. Recalibrate the windows from a real `--embeddings` run before treating embeddings-mode
  band pass-rates as a scorer-quality verdict; until then, the deterministic heuristic calibration is
  the CI-verified guarantee.
- **Cases are synthetic-but-representative.** They use the scorer's real skill vocabulary and the
  real scoring code; they are constructed (not scraped) so the suite is reproducible and shippable in
  a public repo. Expanding with anonymized real postings is the natural next step.
