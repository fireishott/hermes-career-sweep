"""Byparr source - Cloudflare bypass for Indeed, Glassdoor, SimplyHired, Monster, CareerBuilder."""

import re
import requests
import html as html_mod
from sources.utils import clean, ok_title

BYPARR_URL = "http://127.0.0.1:8191/v1"
BYPARR_TIMEOUT = 90000  # ms
REQUEST_TIMEOUT = 100  # seconds


def byparr_get(url):
    """Fetch a page through Byparr Cloudflare solver."""
    r = requests.post(
        BYPARR_URL,
        json={"cmd": "request.get", "url": url, "maxTimeout": BYPARR_TIMEOUT},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "ok":
        return None
    return data.get("solution", {}).get("response", "")


def parse_json_jobs(html_text, title_key="title", company_key="company", location_key="location", url_key="url"):
    """Parse job listings from JSON embedded in HTML."""
    results = []
    if not html_text:
        return results
    # Try multiple JSON patterns
    patterns = [
        rf'"{title_key}"\s*:\s*"(.*?)".*?"{company_key}"\s*:\s*"(.*?)".*?"{location_key}"\s*:\s*"(.*?)".*?"{url_key}"\s*:\s*"(.*?)"',
        rf'"{title_key}"\s*:\s*"(.*?)".*?"{company_key}"\s*:\s*"(.*?)".*?"{location_key}"\s*:\s*"(.*?)"',
    ]
    for m in re.finditer(patterns[0], html_text, re.S):
        title = clean(m.group(1))
        company = clean(m.group(2))
        location = clean(m.group(3))
        url = m.group(4).replace("\\/", "/")
        if ok_title(title):
            results.append({
                "company": company, "title": title, "location": location,
                "url": url if url.startswith("http") else "", "source": "byparr",
            })
    if not results:
        for m in re.finditer(patterns[1], html_text, re.S):
            title = clean(m.group(1))
            company = clean(m.group(2))
            location = clean(m.group(3))
            if ok_title(title):
                results.append({
                    "company": company, "title": title, "location": location,
                    "url": "", "source": "byparr",
                })
    return results


def search_indeed(queries):
    """Search Indeed via Byparr."""
    results = []
    for query in queries:
        url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&l=&fromage=7"
        try:
            html = byparr_get(url)
            if not html:
                continue
            # Indeed embeds job data in JSON
            results.extend(parse_json_jobs(html, "title", "company", "formattedLocation", "viewJobLink"))
            # Fallback: card parsing
            for m in re.finditer(
                r'jobTitle["\s:]+(.*?)["\s].*?companyName["\s:]+(.*?)["\s].*?companyLocation["\s:]+(.*?)["\s]',
                html, re.I | re.S
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": location,
                        "url": "", "source": "indeed",
                    })
        except Exception:
            continue
    return results


def search_glassdoor(queries):
    """Search Glassdoor via Byparr."""
    results = []
    for query in queries:
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query.replace(' ', '+')}&jobType=all&fromAge=7"
        try:
            html = byparr_get(url)
            if not html:
                continue
            results.extend(parse_json_jobs(html, "jobTitle", "employerName", "location", "jobLink"))
        except Exception:
            continue
    return results


def search_simplyhired(queries):
    """Search SimplyHired via Byparr."""
    results = []
    for query in queries:
        url = f"https://www.simplyhired.com/search?q={query.replace(' ', '+')}&l="
        try:
            html = byparr_get(url)
            if not html:
                continue
            results.extend(parse_json_jobs(html))
        except Exception:
            continue
    return results


def search_monster(queries):
    """Search Monster via Byparr."""
    results = []
    for query in queries:
        url = f"https://www.monster.com/jobs/search?q={query.replace(' ', '+')}&where=&page=1&so=m.h.sh"
        try:
            html = byparr_get(url)
            if not html:
                continue
            results.extend(parse_json_jobs(html))
        except Exception:
            continue
    return results


def search_careerbuilder(queries):
    """Search CareerBuilder via Byparr."""
    results = []
    for query in queries:
        url = f"https://www.careerbuilder.com/jobs?keywords={query.replace(' ', '+')}&location="
        try:
            html = byparr_get(url)
            if not html:
                continue
            results.extend(parse_json_jobs(html))
        except Exception:
            continue
    return results


def search_ziprecruiter(queries):
    """Search ZipRecruiter via Byparr."""
    results = []
    for query in queries:
        url = f"https://www.ziprecruiter.com/jobs-search?search={query.replace(' ', '+')}&location="
        try:
            html = byparr_get(url)
            if not html:
                continue
            results.extend(parse_json_jobs(html))
        except Exception:
            continue
    return results


def search_google_jobs(queries):
    """Search Google Jobs via Byparr."""
    results = []
    for query in queries:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}&ibp=htl;jobs"
        try:
            html = byparr_get(url)
            if not html:
                continue
            # Google Jobs embeds structured data
            for m in re.finditer(
                r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)".*?"url"\s*:\s*"(.*?)"',
                html, re.S
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                link = m.group(4).replace("\\/", "/")
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": location,
                        "url": link, "source": "google-jobs",
                    })
        except Exception:
            continue
    return results


# Byparr board configs
QUERIES = [
    "IT Manager",
    "IT Director",
    "Senior IT Manager",
    "IT Operations Manager",
    "Infrastructure Manager",
    "IT Manager Las Vegas",
    "IT Manager remote",
]

BYPARR_BOARDS = {
    "indeed": {"queries": QUERIES, "fn": search_indeed},
    "glassdoor": {"queries": QUERIES, "fn": search_glassdoor},
    "simplyhired": {"queries": QUERIES[:3], "fn": search_simplyhired},
    "monster": {"queries": QUERIES[:3], "fn": search_monster},
    "careerbuilder": {"queries": QUERIES[:3], "fn": search_careerbuilder},
    "ziprecruiter": {"queries": QUERIES[:3], "fn": search_ziprecruiter},
    "google-jobs": {"queries": QUERIES[:4], "fn": search_google_jobs},
}


def scan_byparr_boards():
    """Scan all Byparr-protected boards."""
    all_results = []
    all_errors = []

    for board_name, config in BYPARR_BOARDS.items():
        try:
            results = config["fn"](config["queries"])
            all_results.extend(results)
        except Exception as e:
            all_errors.append(f"{board_name}: {e}")

    return all_results, all_errors
