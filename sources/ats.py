"""ATS API sources - Greenhouse, Ashby, Lever, Workday. Zero-cost, fast, reliable."""

import requests
import re
import html as html_mod
from sources.utils import clean, ok_title, score_title

HEADERS = {"User-Agent": "Mozilla/5.0 career-sweep/2.0"}  # Default for matched but unclassified


def greenhouse(board):
    """Fetch jobs from Greenhouse boards API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=false"
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        jobs = []
        for j in r.json().get("jobs", []):
            title = clean(j.get("title"))
            loc = clean((j.get("location") or {}).get("name") or "Unlisted")
            jobs.append({
                "title": title,
                "location": loc,
                "url": j.get("absolute_url") or j.get("url", ""),
            })
        return jobs
    except Exception:
        return []


def ashby(org):
    """Fetch jobs from Ashby API."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true"
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        jobs = []
        for j in r.json().get("jobs", []):
            loc = j.get("location") or "Unlisted"
            sec = [x.get("location") for x in (j.get("secondaryLocations") or []) if x.get("location")]
            if sec:
                loc += " / " + " / ".join(sec[:3])
            if j.get("isRemote"):
                loc = "Remote - " + loc
            jobs.append({
                "title": clean(j.get("title")),
                "location": clean(loc),
                "url": j.get("jobUrl", ""),
            })
        return jobs
    except Exception:
        return []


def lever(org):
    """Fetch jobs from Lever API."""
    url = f"https://api.lever.co/v0/postings/{org}?mode=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        jobs = []
        for j in r.json():
            cats = j.get("categories") or {}
            loc = clean(cats.get("location") or "Unlisted")
            jobs.append({
                "title": clean(j.get("text")),
                "location": loc,
                "url": j.get("hostedUrl") or j.get("applyUrl", ""),
            })
        return jobs
    except Exception:
        return []


def workday(host, tenant, site):
    """Fetch jobs from Workday API."""
    base = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    jobs = []
    for search in ["IT Manager", "IT Director", "Infrastructure Manager", "IT Operations"]:
        try:
            r = requests.post(
                base,
                json={"appliedFacets": {}, "limit": 100, "offset": 0, "searchText": search},
                headers={**HEADERS, "Content-Type": "application/json"},
                timeout=25,
            )
            if r.status_code != 200:
                continue
            for j in r.json().get("jobPostings", []):
                title = clean(j.get("title"))
                loc = clean(j.get("locationsText") or j.get("location") or "Unlisted")
                url = "https://" + host + clean(j.get("externalPath", ""))
                jobs.append({"title": title, "location": loc, "url": url})
        except Exception:
            continue
    return jobs


def html_page(url):
    """Fallback: scrape job titles from a careers HTML page."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code >= 400:
            return []
        text = r.text
        jobs = []
        for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", text, flags=re.I | re.S):
            attrs, inner = m.groups()
            href_m = re.search(r'href=["\']([^"\']+)', attrs, re.I)
            href = href_m.group(1) if href_m else ""
            label = clean(re.sub(r"<[^>]+>", " ", inner))
            if not label or len(label) > 160:
                continue
            if ok_title(label):
                from urllib.parse import urljoin
                full = urljoin(url, href)
                jobs.append({"title": label, "location": "Unlisted", "url": full})
        return jobs
    except Exception:
        return []


def scan_ats_companies(companies):
    """Scan all ATS companies and return filtered matches."""
    results = []
    errors = []

    for name, provider, slug in companies:
        try:
            if provider == "greenhouse":
                raw = greenhouse(slug)
            elif provider == "ashby":
                raw = ashby(slug)
            elif provider == "lever":
                raw = lever(slug)
            elif provider == "workday":
                parts = slug.split(":")
                raw = workday(parts[0], parts[1], parts[2])
            elif provider == "html":
                raw = html_page(slug)
            else:
                continue

            for j in raw:
                if ok_title(j["title"]):
                    results.append({
                        "company": name,
                        "title": j["title"],
                        "location": j["location"],
                        "url": j["url"],
                        "source": f"ATS:{provider}",
                    })
        except Exception as e:
            errors.append(f"{name}: {e}")

    return results, errors
