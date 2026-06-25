"""Pipeline - dedupe, score, rank job prospects."""

import json
from pathlib import Path
from config import (
    TITLE_NEGATIVES, TOP_COMPANIES,
    US_CITIES, US_SIGNALS, REMOTE_KEYWORDS, INTERNATIONAL_ONLY,
    SCORING, SEEN_FILE, APPLIED_FILE,
)


def load_json(path, default=None):
    """Load JSON file, return default if missing."""
    p = Path(path)
    if not p.exists():
        return default if default is not None else {}
    return json.loads(p.read_text())


def save_json(path, data):
    """Save JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def is_remote_us(loc):
    """Check if location is remote US."""
    if not loc:
        return False
    l = loc.lower()
    has_remote = any(kw in l for kw in REMOTE_KEYWORDS)
    has_us = any(kw in l for kw in US_SIGNALS)
    has_us_city = any(c in l for c in US_CITIES)
    is_intl = any(kw in l for kw in INTERNATIONAL_ONLY) and not has_us and not has_us_city
    if is_intl:
        return False
    if has_remote and (has_us or has_us_city):
        return True
    return False


def is_vegas(loc):
    """Check if location is Las Vegas area."""
    if not loc:
        return False
    return any(kw in loc.lower() for kw in ["las vegas", "nevada", "nv"])


def is_us_city(loc):
    """Check if location mentions a US city (may be onsite)."""
    if not loc:
        return False
    l = loc.lower()
    return any(c in l for c in US_CITIES)


def location_type(loc):
    """Classify location type."""
    if not loc or loc.lower() == "unlisted":
        return "unlisted"
    if is_vegas(loc):
        return "vegas"
    if is_remote_us(loc):
        return "remote_us"
    if is_us_city(loc):
        return "onsite_us"
    return "other"


def passes_location_filter(loc):
    """Check if job passes location filter: remote US, Vegas, or US city."""
    lt = location_type(loc)
    return lt in ("vegas", "remote_us", "onsite_us", "unlisted")


def score_job(title, company, location):
    """Score a job for relevance. Higher = better match."""
    from sources.utils import score_title
    t = title.lower()
    c = company.lower().split(" /")[0].split(" (")[0].strip()
    s = score_title(title)

    # Location bonuses
    lt = location_type(location)
    if lt == "vegas":
        s += SCORING["vegas_bonus"]
    elif lt == "remote_us":
        s += SCORING["remote_bonus"]

    # Top company
    if c in TOP_COMPANIES:
        s += SCORING["top_company_bonus"]

    # Junior penalty
    for neg in TITLE_NEGATIVES[:5]:
        if neg in t:
            s += SCORING["junior_penalty"]
            break

    return max(0, s)


def score_label(score):
    """Convert numeric score to label."""
    if score >= 15:
        return "HIGH"
    elif score >= 8:
        return "MEDIUM"
    return "LOW"


def deduplicate(jobs, seen=None, applied=None):
    """Remove duplicates based on URL and company+title combos."""
    if seen is None:
        seen = load_json(SEEN_FILE, [])
    if applied is None:
        applied = load_json(APPLIED_FILE, [])

    seen_set = set(seen)
    applied_set = set(applied)

    unique = []
    seen_keys = set()

    for j in jobs:
        url = j.get("url", "")
        company = j.get("company", "").lower().strip()
        title = j.get("title", "").lower().strip()

        if url in applied_set:
            continue
        if url in seen_set:
            continue

        key = f"{company}|{title}"
        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique.append(j)

    return unique


def update_seen(jobs):
    """Add job URLs to seen list."""
    seen = load_json(SEEN_FILE, [])
    seen_set = set(seen)
    for j in jobs:
        url = j.get("url", "")
        if url:
            seen_set.add(url)
    save_json(SEEN_FILE, list(seen_set))


def passes_title_filter(title):
    """Check if title passes the target role filter."""
    from sources.utils import ok_title
    return ok_title(title)


def rank_jobs(jobs):
    """Score, filter, and rank jobs."""
    scored = []
    for j in jobs:
        loc = j.get("location", "")
        title = j.get("title", "")

        if not passes_location_filter(loc):
            continue
        if not passes_title_filter(title):
            continue

        score = score_job(title, j["company"], loc)
        lt = location_type(loc)
        scored.append({
            **j,
            "score": score,
            "label": score_label(score),
            "location_type": lt,
        })

    scored.sort(key=lambda x: (-x["score"], x["company"]))
    return scored
