#!/usr/bin/env python3
"""Autonomous board collection for career-sweep.

Pulls direct-request job boards (Dice, RemoteOK, BuiltIn, Remotive, etc.) using
plain HTTP requests -- NO agent / web_extract / browser needed. Merges the
results into data/board-results-YYYY-MM-DD.json, preserving any rows an agent
already wrote there via web_extract, and dedupes by URL. Safe to run repeatedly.

This is what makes the sweep runnable end-to-end by a weak model or by cron:
the board-finding step no longer requires the agent to reason.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from sources.direct import scan_direct_boards  # noqa: E402

DATA = ROOT / "data"
D = datetime.now().strftime("%Y-%m-%d")
OUT = DATA / f"board-results-{D}.json"

# Preserve anything already collected today (e.g. agent web_extract enrichment).
existing = []
if OUT.exists():
    try:
        existing = json.loads(OUT.read_text()) or []
    except Exception:
        existing = []

results, errors = scan_direct_boards()


def norm(j):
    """Coerce a board row to the 5-field schema the pipeline expects."""
    return {
        "company": (j.get("company") or "").strip(),
        "title": (j.get("title") or "").strip(),
        "location": (j.get("location") or "Unlisted").strip() or "Unlisted",
        "url": (j.get("url") or "").strip(),
        "source": (j.get("source") or "direct").strip(),
    }


combined = [norm(j) for j in existing] + [norm(j) for j in results]

seen, deduped = set(), []
for j in combined:
    key = j["url"] or (j["company"] + "|" + j["title"])
    if not key or key in seen:
        continue
    seen.add(key)
    deduped.append(j)

DATA.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(deduped, indent=2))

print(
    f"collect_boards: {len(results)} from direct boards + {len(existing)} pre-existing "
    f"-> {len(deduped)} unique written to data/{OUT.name}"
)
if errors:
    shown = "; ".join(errors[:4]) + (" ..." if len(errors) > 4 else "")
    print(f"  ({len(errors)} board errors/blocks, expected: {shown})")
