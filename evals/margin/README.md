# Margin cost-per-outcome eval suite — `jobscraper-fit-scoring`

This suite gives [Margin](https://github.com/subhsubh24/Margin.ai) an **accurate, statistical**
cost-per-outcome for JobScraper's job-fit scoring — measured over a representative input matrix,
not a single hand-picked request.

## What's here

| File | Role |
| --- | --- |
| `fit_scoring_cases.jsonl` | 60 real job+candidate pairs across the full fit spectrum (15 each: strong / partial / weak / mismatch) × varied roles, seniority, industries. |
| `bands.json` | The grader's expected-fit-band → score-window table. |
| `../../scripts/margin_eval.py` | The runner: scores every case through the REAL path, grades it, emits calls + graded outcomes to Margin via the `margin-meter` SDK. |
| `../../tests/evals/test_margin_eval_suite.py` | The keyless, network-free CI guard (integrity + calibration). |

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
`quality_score=<score/100>`, `quality_method="eval-band-grader"`, `session_id="eval:<run-id>"`.

## Two modes

- **Heuristic (default, key-free).** `score_job` runs locally (semantic baseline 0.5, so
  `overall = 30 + 40·skills_score`). There is **no third-party LLM call and no AI cost** — an
  honest zero-cost baseline. Because it's deterministic, the grader is fully **calibrated** and the
  CI test verifies every case lands in-band with no network.
- **Embeddings (`--embeddings`, needs `GEMINI_API_KEY`).** `score_job` uses **real Gemini
  embeddings** for the semantic half. The runner meters each embedding call (real tokens → real
  cost), so the emitted cost-per-outcome reflects the actual **paid** path. Cost-capped by
  `--max-embed-cases` (default 40).

## How to run

```bash
# 1) Dry run — score + grade + print a summary, emit nothing (no network):
python scripts/margin_eval.py --dry-run

# 2) Emit to Margin (heuristic; zero AI cost baseline). Reads the SDK's env internally:
export MARGIN_INGEST_URL="https://<your-margin-deployment>"
export MARGIN_INGEST_KEY="mgk_..."          # per-project ingest key
python scripts/margin_eval.py

# 3) REAL metered cost-per-outcome (paid embeddings path), cost-capped:
export GEMINI_API_KEY="..."
python scripts/margin_eval.py --embeddings --max-embed-cases 30

# 4) Re-run with a model/config override (e.g. to compare embedding models):
python scripts/margin_eval.py --embeddings --embedding-model gemini-embedding-001 --run-id compare-a
```

Every batch is tagged `session_id="eval:<run-id>"` so eval traffic is separable from production in
Margin. The runner is **fail-safe**: missing SDK or missing `MARGIN_INGEST_URL`/`MARGIN_INGEST_KEY`
→ telemetry disabled (still scores, grades, prints); missing `GEMINI_API_KEY` → heuristic mode.

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
