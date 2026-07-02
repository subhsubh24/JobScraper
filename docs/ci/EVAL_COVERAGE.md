# EVAL COVERAGE — every AI-output feature is evaluated (and judged on REAL output)

The self-validation gate (`check_validation.py`) proves each capability RUNS; this tracks
whether each AI-output feature's OUTPUT is any good. Enforced by `scripts/check_eval_coverage.py`
(required, in `preflight`): a NEW LLM-using module in `src/` cannot ship without an entry here
that names both a deterministic eval AND a real-output eval — so eval coverage GROWS with the
product instead of drifting behind it.

- **deterministic_evals** — golden/structure evals that pin behavior with a fake LLM (fast,
  key-free, run everywhere).
- **real_output_eval** — judges the ACTUAL Gemini output (substantive / on-topic / structured);
  runs in CI when `GEMINI_API_KEY` is set (skips locally without a key). Required for every
  AI-output feature (the "real on all features" ratchet).

```yaml
EVAL_COVERAGE:
  - feature: fit-scoring
    modules: [src/ranking/scorer.py]
    deterministic_evals: [tests/evals/test_scoring_evals.py]
    real_output_eval: tests/evals/test_ai_output_evals.py   # real embedding path -> valid score
  - feature: prep-pack
    modules: [src/enrichment/llm_workflows.py]
    deterministic_evals: [tests/evals/test_prep_pack_evals.py]
    real_output_eval: tests/evals/test_ai_output_evals.py   # real prep pack: substantive + structured
  - feature: coach
    modules: [src/ai_coach/career_coach.py]
    deterministic_evals: [tests/evals/test_suggestions_evals.py]
    real_output_eval: tests/evals/test_ai_output_evals.py   # real answer: substantive + on-topic
```

Adding a new AI feature? Add its module to a feature entry (or a new entry) with a deterministic
eval + a real-output eval, or the gate fails. Real-output judging deliberately uses tolerant
assertions (length / relevance / structure / safety), not exact strings — an LLM-as-judge scorer
is a future upgrade, but must stay non-flaky before it gates.
