"""
parser.py — MaiConverter wrapper for maimai Skill Gap Analyzer.

MaiConverter API summary (v0.14.5):
- `maiconverter.simai.parse_file(path)` → (title, [(chart_num, SimaiChart), ...])
  Parses a full maidata.txt (with metadata header + multiple difficulty charts).
- `SimaiChart.notes` → list of note objects (TapNote, HoldNote, SlideNote,
  TouchTapNote, TouchHoldNote).
- `SimaiChart.bpms` → list of BPM events, each with `.bpm` and `.measure`.
- `SimaiChart.measure_to_second(measure)` → converts a measure number to seconds,
  accounting for BPM changes.
- Note types are distinguished by `note.note_type` (NoteType enum) or by
  isinstance checks against the concrete classes.
  - Tap-family: NoteType.tap, break_tap, star, break_star, ex_tap, ex_star
  - Hold-family: NoteType.hold, ex_hold
  - Slide: NoteType.complete_slide
  - Touch (DX): NoteType.touch_tap, touch_hold
"""

from __future__ import annotations

import io
import re
import sys
from contextlib import contextmanager
from typing import Optional

from maiconverter.simai import parse_file_str


@contextmanager
def _suppress_stdout():
    """Suppress maiconverter's 'Parsing chart #N...Done' noise."""
    old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = old
from maiconverter.simai.simainote import TapNote, HoldNote, SlideNote, TouchHoldNote
from maiconverter.event import NoteType


def _preprocess_simai(text: str) -> str:
    """Normalize simai text so maiconverter can parse it.

    Fixes common issues in the wild:
    - UTF-8 BOM at start of file.
    - Windows line endings (\r\n) — normalize to \n.
    - Empty metadata fields (e.g. ``&des=``) — the Lark grammar requires a
      STRING token after ``=``, so we drop lines whose value is blank.
    """
    text = text.lstrip("﻿")  # strip UTF-8 BOM
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^&[a-zA-Z0-9_]+=\s*$", stripped):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


# Slide direction characters in simai fragment notation.
_SLIDE_CHARS = frozenset("-^<>szvwpqV@")


def _fallback_parse(raw_simai: str) -> dict:
    """Regex-based note counter used when maiconverter cannot parse the file.

    Handles modern simai notation (chained paths, bx/bn modifiers, etc.) that
    maiconverter 0.14.5 rejects.  Counts are approximate but good enough for
    the downstream Claude analyzer.
    """
    # --- BPM from metadata ---
    bpm = 0.0
    m = re.search(r"&bpm\s*=\s*([0-9.]+)", raw_simai)
    if m:
        bpm = float(m.group(1))

    # --- Find the highest &inote_N= section ---
    # Each section runs from &inote_N= up to the next &-tag or end of string.
    chart_text = ""
    highest_n = -1
    for m in re.finditer(r"&inote_(\d+)\s*=\s*(.*?)(?=\n&|\Z)", raw_simai, re.DOTALL):
        n = int(m.group(1))
        if n > highest_n:
            highest_n = n
            chart_text = m.group(2)

    if not chart_text:
        return {
            "total_notes": 0, "tap_count": 0, "hold_count": 0, "slide_count": 0,
            "bpm": bpm, "duration_seconds": 0.0, "raw_simai": raw_simai,
        }

    # --- BPM from chart if not in metadata ---
    if bpm == 0.0:
        m = re.search(r"\(([0-9.]+)\)", chart_text)
        if m:
            bpm = float(m.group(1))

    # --- Strip control tokens and whitespace ---
    clean = re.sub(r"\([0-9.]+\)", "", chart_text)   # (BPM) markers
    clean = re.sub(r"\{[0-9.]+\}", "", clean)          # {divisor} markers
    clean = re.sub(r"\[[^\]]*\]", "", clean)            # [duration] markers
    clean = re.sub(r"[ \t\r\n]+", "", clean)

    tap_count = 0
    hold_count = 0
    slide_count = 0

    _TOUCH_RE = re.compile(r"^[CBAED][0-9]")

    for slot in clean.split(","):
        slot = slot.strip()
        if not slot or slot == "E":
            continue
        for elem in slot.split("/"):
            elem = elem.strip()
            if not elem or elem == "E":
                continue
            if _TOUCH_RE.match(elem):
                if "h" in elem:
                    hold_count += 1
                else:
                    tap_count += 1
                continue
            if elem and elem[0] in "12345678":
                # Strip leading-position modifiers to find slide direction.
                rest = elem[1:].lstrip("bex$@?!n")
                if rest and rest[0] in _SLIDE_CHARS:
                    slide_count += 1
                elif "h" in elem:
                    hold_count += 1
                else:
                    tap_count += 1

    total_notes = tap_count + hold_count + slide_count

    # Duration: rough estimate from note density at the chart's BPM.
    duration_seconds = 0.0
    if bpm > 0 and total_notes > 0:
        duration_seconds = round(total_notes / bpm * 60.0, 3)

    return {
        "total_notes": total_notes,
        "tap_count": tap_count,
        "hold_count": hold_count,
        "slide_count": slide_count,
        "bpm": bpm,
        "duration_seconds": duration_seconds,
        "raw_simai": raw_simai,
    }


# NoteType values that count as "tap" for our purposes (includes star/break variants
# and touch taps, but excludes hold and slide types).
_TAP_TYPES = {
    NoteType.tap,
    NoteType.break_tap,
    NoteType.star,
    NoteType.break_star,
    NoteType.ex_tap,
    NoteType.ex_star,
    NoteType.touch_tap,
}

_HOLD_TYPES = {
    NoteType.hold,
    NoteType.ex_hold,
    NoteType.touch_hold,
}

_SLIDE_TYPES = {
    NoteType.complete_slide,
}


def _pick_chart(charts):
    """Return the highest-difficulty SimaiChart available (highest chart number)."""
    if not charts:
        return None
    return max(charts, key=lambda pair: pair[0])[1]


def _extract_bpm_from_raw(raw_simai: str) -> Optional[float]:
    """Fallback: parse &bpm= tag from raw simai text."""
    match = re.search(r"&bpm\s*=\s*([0-9.]+)", raw_simai)
    if match:
        return float(match.group(1))
    return None


def parse(maidata_path: str) -> dict:
    """Parse a maidata.txt (simai format) file and return note statistics.

    Args:
        maidata_path: Absolute or relative path to a maidata.txt file.

    Returns:
        A dict with keys:
            total_notes     (int)   — total playable notes
            tap_count       (int)   — tap / touch-tap notes (including stars/breaks)
            hold_count      (int)   — hold / touch-hold notes
            slide_count     (int)   — slide notes
            bpm             (float) — initial (first) BPM of the chart
            duration_seconds (float) — estimated chart duration in seconds
            raw_simai       (str)   — full text of the file

    Raises:
        ValueError: If the file cannot be parsed.
    """
    # Always read the raw text — this must succeed even if MaiConverter fails.
    with open(maidata_path, "r", encoding="utf-8", errors="replace") as fh:
        raw_simai = fh.read()

    try:
        cleaned = _preprocess_simai(raw_simai)
        with _suppress_stdout():
            _title, charts = parse_file_str(cleaned)
    except Exception:
        # maiconverter can't handle modern simai notation — use regex fallback.
        return _fallback_parse(raw_simai)

    # Pick the hardest difficulty chart (highest inote_N number).
    chart = _pick_chart(charts)

    if chart is None:
        # No chart data found — return zeroed stats with raw text.
        bpm_fallback = _extract_bpm_from_raw(raw_simai) or 0.0
        return {
            "total_notes": 0,
            "tap_count": 0,
            "hold_count": 0,
            "slide_count": 0,
            "bpm": bpm_fallback,
            "duration_seconds": 0.0,
            "raw_simai": raw_simai,
        }

    tap_count = 0
    hold_count = 0
    slide_count = 0

    for note in chart.notes:
        nt = note.note_type
        if nt in _TAP_TYPES:
            tap_count += 1
        elif nt in _HOLD_TYPES:
            hold_count += 1
        elif nt in _SLIDE_TYPES:
            slide_count += 1
        # start_slide / end_slide are SDT-internal and not counted separately.

    total_notes = tap_count + hold_count + slide_count

    # BPM: use the first (starting) BPM event.
    bpm = 0.0
    if chart.bpms:
        chart.bpms.sort(key=lambda b: b.measure)
        bpm = float(chart.bpms[0].bpm)
    else:
        bpm = _extract_bpm_from_raw(raw_simai) or 0.0

    # Duration: find the last note's measure, then convert to seconds.
    # For holds/slides we account for their duration so we get the true end time.
    duration_seconds = 0.0
    if chart.notes:
        last_measure = 0.0
        for note in chart.notes:
            end_measure = note.measure
            if hasattr(note, "duration"):
                # SlideNote duration includes delay, HoldNote is plain duration.
                if isinstance(note, SlideNote):
                    end_measure += note.delay + note.duration
                else:
                    end_measure += note.duration
            last_measure = max(last_measure, end_measure)

        try:
            duration_seconds = chart.measure_to_second(last_measure)
        except Exception:
            # measure_to_second can raise if BPMs are malformed; fall back to
            # a rough estimate using the first BPM.
            if bpm > 0:
                # Each measure = 4 beats at the current time signature.
                duration_seconds = (last_measure - 1.0) * (60.0 / bpm) * 4
            else:
                duration_seconds = 0.0

    return {
        "total_notes": total_notes,
        "tap_count": tap_count,
        "hold_count": hold_count,
        "slide_count": slide_count,
        "bpm": bpm,
        "duration_seconds": round(duration_seconds, 3),
        "raw_simai": raw_simai,
    }
