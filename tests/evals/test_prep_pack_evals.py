"""Eval for the prep-pack generator's persistence path (Track E).

generate_prep_pack is a monetized feature (gated behind the Pro/Premium prep limit) but had no
test on its STRUCTURE/persistence. The LLM call is the only non-deterministic part, so we patch
it with a fake client and assert the PrepArtifact is persisted with the right shape — fully
deterministic, no Gemini key. This guards the artifact contract (type/title/content/model).
"""
from src.db.models import JobPosting, PrepArtifact, User, UserTier
from src.enrichment.llm_workflows import LLMWorkflows


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        class _M:
            content = self._content

        class _C:
            message = _M()

        class _R:
            choices = [_C()]

        return _R()


def _seed(db):
    user = User(email="prep@example.com", password_hash="x", tier=UserTier.PREMIUM, resume_text="python react")
    db.add(user)
    db.flush()
    job = JobPosting(user_id=user.id, title="Backend Engineer", company_name="Acme", description="python role")
    db.add(job)
    db.flush()
    return user, job


def test_generate_prep_pack_persists_artifact(db_session):
    user, job = _seed(db_session)
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM("## 1. Company Research\nAcme builds things.\n## 4. Technical Questions\n...")

    artifact = wf.generate_prep_pack(job, user)

    assert isinstance(artifact, PrepArtifact)
    assert artifact.artifact_type == "prep_pack"
    assert artifact.job_id == job.id
    assert "Backend Engineer" in artifact.title and "Acme" in artifact.title
    assert artifact.content and "Company Research" in artifact.content
    assert artifact.model_used  # records which model produced it

    # It is actually persisted (queryable on the same session), exactly once.
    rows = db_session.query(PrepArtifact).filter(PrepArtifact.job_id == job.id).all()
    assert len(rows) == 1 and rows[0].artifact_type == "prep_pack"


# A realistic, deterministic golden prep-pack (what a healthy generation looks like). Used to
# assert the PERSISTED artifact is substantive, structured, and grounded — not just that a row
# exists. This is the per-PR content-quality guard: it runs key-free and reddens if the
# generation PIPELINE (the refine pass, moderation, or persistence) ever degrades a healthy
# model output into a stub / unstructured / truncated artifact. It deliberately does NOT judge
# whether the LIVE model actually grounds its output — that is the nightly, live-keyed
# real-output eval's job (tests/evals/test_ai_output_evals.py); here the input is fixed so the
# only thing under test is our own pipeline preserving a good output faithfully.
_GOLDEN_PREP_PACK = """## 1. Company Research Summary
Acme is a backend infrastructure company. Recent news signals aggressive hiring on the
platform team; the JD emphasises reliability and scale.

## 2. Role Analysis
The Backend Engineer role centres on service reliability. Must-have: Python and REST APIs;
nice-to-have: React for internal tooling.

## 3. Your Fit Story
Lead with your Python services experience and your React internal-dashboard work — both map
directly to Acme's stated stack. Address the gap in large-scale on-call proactively.

## 4. Technical Interview Questions
1. Design a rate limiter for a multi-tenant API. (framework: clarify → data model → tradeoffs)
2. How would you debug elevated p99 latency on a Python service under load?

## 5. Behavioral Interview Questions
1. Tell me about a time you owned an incident end to end. (STAR: situation → task → action → result)
2. Describe a disagreement with a senior engineer and how you resolved it.

## 6. Questions to Ask Them
1. What does the on-call rotation look like for the platform team?
2. How does Acme measure backend reliability today?

## 7. 48-Hour Study Plan
- Day 1: revisit Python concurrency and API design; skim Acme's public engineering blog.
- Day 2: mock two system-design questions out loud; prepare three STAR stories.
"""


def test_generated_prep_pack_content_is_substantive_structured_and_grounded(db_session):
    """Per-PR (key-free) content-quality guard on the persisted prep pack.

    Feeds a realistic golden generation through the REAL generate_prep_pack pipeline (refine +
    moderation + persistence) and asserts the stored artifact is substantive, keeps its markdown
    structure, references the actual job, and preserves the candidate's real skills — so a
    pipeline regression that truncates, strips, or unstructures a healthy output reddens here
    instead of only in the nightly live eval.
    """
    user, job = _seed(db_session)  # Backend Engineer @ Acme; résumé "python react"
    wf = LLMWorkflows(db_session)
    wf.client = _FakeLLM(_GOLDEN_PREP_PACK)

    content = wf.generate_prep_pack(job, user).content
    low = content.lower()

    # SUBSTANTIVE — not a stub the pipeline degraded to.
    assert len(content) > 600, f"prep pack too short ({len(content)} chars) — pipeline stubbed it"
    # STRUCTURED — the requested markdown survived refine/moderation/persist.
    assert content.count("##") >= 5, f"prep pack lost its section structure ({content.count('##')} headings)"
    # JOB-RELEVANT — references the actual posting, not generic boilerplate.
    assert any(t in low for t in ("backend", "acme", "engineer")), "prep pack doesn't reference the job"
    # CANDIDATE-GROUNDED — the résumé skills the drafter was given are preserved, not dropped.
    assert any(t in low for t in ("python", "react")), "prep pack dropped the candidate's real skills"
