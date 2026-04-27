"""
analyzer.py — Claude API integration for maimai Skill Gap Analyzer.

Provides analyze(features: dict) -> dict, which calls Claude to tag a
maimai chart with skill labels and estimate its difficulty on the maimai
scale (1.0 – 15.0).

Environment:
    ANTHROPIC_API_KEY  — must be set before importing this module.
"""

import anthropic
import json

# Module-level client — reads ANTHROPIC_API_KEY from environment.
client = anthropic.Anthropic()

# ---------------------------------------------------------------------------
# Tag taxonomy (used verbatim in the prompt)
# ---------------------------------------------------------------------------
TAGGING_PROMPT = """\
You are a maimai chart analyst. Given the raw simai chart text and note \
statistics below, identify the dominant skill patterns and estimate the chart \
difficulty.

TAG TAXONOMY — choose 1 to 3 tags from this list ONLY (no other tags allowed):
  - Trill          : rapid alternating single-finger hits between two positions
  - Stream         : long sequences of consecutive tap notes
  - Stamina        : high density charts requiring sustained energy throughout
  - Tech/Crossover : complex hand crossing patterns requiring technique
  - Slide-Heavy    : charts dominated by slide note patterns
  - Hand-Alternation: patterns requiring alternating between left and right hands
  - Balanced       : no single dominant pattern; well-rounded chart

DIFFICULTY SCALE: 1.0 (easiest) to 15.0 (hardest) on the maimai rating scale.

Return JSON ONLY — no markdown fences, no commentary — in exactly this format:
{"tags": ["Tag1", "Tag2"], "difficulty": 9.5}
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_TAG_PRIORITY = [
    "Trill", "Slide-Heavy", "Stream", "Stamina",
    "Tech/Crossover", "Hand-Alternation", "Balanced",
]


def rule_analyze(features: dict) -> dict:
    """Deterministic, zero-cost tagger used for batch DB population.

    Returns the same shape as analyze() so batch_tag.py needs no other changes.
    """
    total = features["total_notes"] or 1
    tap_r = features["tap_count"] / total
    hold_r = features["hold_count"] / total
    slide_r = features["slide_count"] / total
    dur = features["duration_seconds"] or 1.0
    density = total / dur          # notes per second
    bpm = features["bpm"] or 120.0

    tags: list[str] = []

    if slide_r > 0.30:
        tags.append("Slide-Heavy")

    if bpm >= 170 and tap_r > 0.65 and density > 9:
        tags.append("Trill")

    if tap_r > 0.60 and density > 6 and "Trill" not in tags:
        tags.append("Stream")

    if dur > 100 or (density > 5 and total > 700):
        tags.append("Stamina")

    if slide_r > 0.15 and hold_r > 0.10 and density > 4:
        tags.append("Tech/Crossover")

    if 0.45 <= tap_r <= 0.72 and slide_r < 0.25 and density > 5:
        tags.append("Hand-Alternation")

    # Deduplicate, sort by priority, cap at 3
    seen: set[str] = set()
    ordered: list[str] = []
    for t in _TAG_PRIORITY:
        if t in tags and t not in seen:
            ordered.append(t)
            seen.add(t)
    tags = ordered[:3] or ["Balanced"]

    # Use in-game level tag if available (lv_5/lv_4 in maidata.txt).
    if features.get("level") is not None:
        difficulty = features["level"]
    else:
        base = min(density * 1.8 + 2.0, 13.0)
        bpm_bonus = max(0.0, (bpm - 150.0) / 80.0)
        note_bonus = min(total / 500.0, 1.5)
        slide_bonus = slide_r * 1.5
        raw = base + bpm_bonus + note_bonus + slide_bonus
        difficulty = round(min(max(raw, 1.0), 15.0) * 2) / 2

    return {"tags": tags, "difficulty": difficulty}


def analyze(features: dict) -> dict:
    """Analyze a parsed maimai chart and return skill tags + difficulty.

    Args:
        features: dict as returned by parser.parse(), containing at minimum:
            raw_simai        (str)   — full simai chart text
            total_notes      (int)
            tap_count        (int)
            hold_count       (int)
            slide_count      (int)
            bpm              (float)
            duration_seconds (float)

    Returns:
        {"tags": list[str], "difficulty": float | None}
        Falls back to {"tags": ["Balanced"], "difficulty": None} on any
        JSON parse error from the model.
    """
    # Build the prompt manually (f-string) to avoid .format() choking on
    # the {N} divisor markers that appear in raw simai text.
    note_stats = (
        f"total_notes={features['total_notes']}, "
        f"tap_count={features['tap_count']}, "
        f"hold_count={features['hold_count']}, "
        f"slide_count={features['slide_count']}"
    )
    prompt = (
        TAGGING_PROMPT
        + "\n\n--- NOTE STATISTICS ---\n"
        + note_stats
        + f"\nbpm={features['bpm']}, duration_seconds={features['duration_seconds']}"
        + "\n\n--- RAW SIMAI CHART ---\n"
        + features["raw_simai"]
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()

    try:
        result = json.loads(raw_text)
        return {
            "tags": result["tags"],
            "difficulty": float(result["difficulty"]),
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {"tags": ["Balanced"], "difficulty": None}
