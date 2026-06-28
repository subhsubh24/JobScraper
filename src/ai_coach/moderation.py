"""Content safety guardrail for the AI Career Coach.

WHY: Apple App Store Review §1.2 (and Google Play's UGC/AI policy) require apps that surface
AI-generated content to filter objectionable material and handle harmful user input
responsibly. This module is the programmatic filter that backs that requirement — applied to
BOTH the user's message (before we spend an LLM call) and the model's output (a safety net in
case the model ignores the system-prompt guidance).

DESIGN PRINCIPLES:
- Dependency-free, deterministic regex classifier — runs in CI with no key, so the guarantee
  is testable (a green test proves the filter actually fires).
- CONSERVATIVE by intent: a career coach must keep discussing legitimately sensitive career
  topics ("sexual harassment at work", "my toxic manager", "I'm burned out / depressed about
  rejections", "negotiate aggressively"). The patterns are written to NOT trip on those — a
  false block of a real career question is itself a product failure.
- Self-harm is treated with care, not a cold refusal: we respond with empathy + real crisis
  resources rather than engaging the model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Crisis resources shown when a user expresses self-harm intent. Kept generic/international
# so it's appropriate regardless of locale; 988 is US, with an international pointer.
CRISIS_RESPONSE = (
    "I'm really sorry you're feeling this way — that sounds genuinely hard, and you deserve "
    "support from someone trained to help. I'm a career coach and not able to provide crisis "
    "counseling, but please reach out right now:\n\n"
    "• US: call or text 988 (Suicide & Crisis Lifeline), available 24/7\n"
    "• UK & ROI: call Samaritans at 116 123\n"
    "• Elsewhere: find a local helpline at https://findahelpline.com\n\n"
    "If you're in immediate danger, please call your local emergency number. When you're "
    "ready, I'm here to help with your job search."
)

DECLINE_RESPONSE = (
    "I can't help with that — I'm a career coach, so I keep our conversation focused on your "
    "job search, interviews, résumé, salary, and career decisions. Ask me anything in that "
    "space and I'm glad to dig in."
)

# --- Self-harm: require explicit self-directed harm intent, exclude common hyperbole. ---
_SELF_HARM = re.compile(
    r"\b("
    r"kill(ing)? myself|"
    r"end(ing)? my (own )?life|"
    r"take (my|my own) life|"
    r"want(ing)? to die|"
    r"wanna die|"
    r"i('?m| am)? .{0,15}suicidal|"
    r"suicidal( thoughts| ideation)|"
    r"commit(ting)? suicide|"
    r"(hurt|harm|cut|cutting) (myself|my self)|"
    r"don'?t want to (live|be alive|exist) (any ?more|anymore)?"
    r")\b",
    re.IGNORECASE,
)
# Hyperbole that should NEVER trigger the crisis path (career venting, idioms).
_SELF_HARM_FALSE_POSITIVE = re.compile(
    r"\b("
    r"killing it|kill(ing)? for|dying to|dead tired|"
    r"this (job|commute|interview|process) is killing me|"
    r"killing my (vibe|mood)"
    r")\b",
    re.IGNORECASE,
)

# --- Requests to direct serious physical harm at a real person. ---
_VIOLENCE = re.compile(
    r"\b("
    r"how (do|can|to) .{0,30}(make|build|create) .{0,15}(bomb|explosive|weapon)|"
    r"(kill|murder|stab|shoot|poison|attack) (my |the )?"
    r"(boss|manager|coworker|co-worker|colleague|him|her|them|someone)|"
    r"(hurt|harm) .{0,15}(physically)|"
    r"get (violent )?revenge on"
    r")\b",
    re.IGNORECASE,
)

# --- Requests to GENERATE hateful/sexual content (NOT discussing harassment as a topic). ---
_HATE_GEN = re.compile(
    r"\b(write|generate|give me|make|create|compose)\b.{0,40}\b"
    r"(racist|sexist|homophobic|transphobic|antisemitic|hateful|bigoted)\b.{0,20}\b"
    r"(joke|jokes|rant|message|insult|content|slur|slurs)\b",
    re.IGNORECASE,
)
_SEXUAL_GEN = re.compile(
    r"\b(write|generate|describe|tell me|give me|make|create)\b.{0,30}\b"
    r"(erotic|sexually explicit|porn|pornographic|nsfw|sex scene|sexual fantasy)\b",
    re.IGNORECASE,
)

# --- Output safety net: catch the model emitting actionable harmful instructions. ---
_OUTPUT_UNSAFE = re.compile(
    r"\b("
    r"here('?s| is) how to (make|build) a (bomb|weapon|explosive)|"
    r"step-by-step .{0,20}(suicide|kill yourself)|"
    r"you should (kill|hurt|harm) (yourself|them|him|her)"
    r")\b",
    re.IGNORECASE,
)


@dataclass
class ModerationResult:
    allowed: bool
    category: Optional[str] = None  # 'self_harm' | 'violence' | 'hate' | 'sexual' | 'unsafe_output'
    safe_response: Optional[str] = None  # what to return INSTEAD when not allowed


_ALLOWED = ModerationResult(allowed=True)


class ContentModerator:
    """Deterministic, conservative safety classifier for coach input and output."""

    def check_input(self, message: str) -> ModerationResult:
        if not message:
            return _ALLOWED
        if _SELF_HARM.search(message) and not _SELF_HARM_FALSE_POSITIVE.search(message):
            return ModerationResult(False, "self_harm", CRISIS_RESPONSE)
        if _VIOLENCE.search(message):
            return ModerationResult(False, "violence", DECLINE_RESPONSE)
        if _HATE_GEN.search(message):
            return ModerationResult(False, "hate", DECLINE_RESPONSE)
        if _SEXUAL_GEN.search(message):
            return ModerationResult(False, "sexual", DECLINE_RESPONSE)
        return _ALLOWED

    def check_output(self, text: str) -> ModerationResult:
        """Safety net on the model's reply. Conservative: only replaces clearly unsafe output
        so a normal coaching answer is never silently swallowed."""
        if text and _OUTPUT_UNSAFE.search(text):
            return ModerationResult(False, "unsafe_output", DECLINE_RESPONSE)
        return _ALLOWED
