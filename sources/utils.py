"""Shared utilities for career sweep sources."""

import re
import html as html_mod
from config import LEADERSHIP_TERMS, DOMAIN_TERMS, EXACT_PHRASES, TITLE_NEGATIVES, TITLE_SCORES


def clean(s):
    """Unescape HTML, strip tags, collapse whitespace."""
    if not s:
        return ""
    s = html_mod.unescape(str(s))
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def ok_title(title):
    """Check if title matches target roles and isn't negative."""
    t = title.lower()
    if any(neg in t for neg in TITLE_NEGATIVES):
        return False

    # Exact phrases match on their own
    if any(phrase in t for phrase in EXACT_PHRASES):
        return True

    # Leadership + Domain two-part match
    has_leadership = any(lt in t for lt in LEADERSHIP_TERMS)
    has_domain = any(re.search(r'\b' + re.escape(dt) + r'\b', t) for dt in DOMAIN_TERMS)

    if has_leadership and has_domain:
        return True

    return False


def score_title(title):
    """Score a title based on leadership level."""
    t = title.lower()
    for kw, score in TITLE_SCORES.items():
        if kw in t:
            return score
    return 5
