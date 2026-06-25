"""Direct request sources - boards that don't need stealth. APIs, RSS, simple HTML."""

import re
import json
import requests
import html as html_mod
from sources.utils import clean, ok_title

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"}


def search_dice(queries):
    """Search Dice. Returns HTML, parse job cards."""
    results = []
    for query in queries:
        url = f"https://www.dice.com/jobs?q={query.replace(' ', '+')}&radius=30&radiusUnit=mi&page=1&pageSize=20&language=en"
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                continue
            text = r.text
            # Dice renders via Next.js, look for JSON data in script tags
            for m in re.finditer(r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)"', text, re.S):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": location,
                        "url": url, "source": "dice",
                    })
            # Also try card-style parsing
            for m in re.finditer(r'<a[^>]*data-testid="job-card[^"]*"[^>]*href="([^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<span[^>]*>(.*?)</span>', text, re.I | re.S):
                link = m.group(1)
                title = clean(m.group(2))
                company = clean(m.group(3))
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": "Unlisted",
                        "url": link if link.startswith("http") else "https://www.dice.com" + link,
                        "source": "dice",
                    })
        except Exception:
            continue
    return results


def search_remoteok():
    """Search RemoteOK (JSON API)."""
    results = []
    try:
        r = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        data = r.json()
        for j in data:
            title = j.get("position", "")
            if not title:
                continue
            company = j.get("company", "")
            location = j.get("location", "Remote") or "Remote"
            url = j.get("url", "")
            if not url:
                slug = j.get("slug", "")
                url = f"https://remoteok.com/remote-jobs/{slug}" if slug else ""
            if ok_title(title):
                results.append({
                    "company": company, "title": title, "location": location,
                    "url": url, "source": "remoteok",
                })
    except Exception:
        pass
    return results


def search_remotive():
    """Search Remotive (JSON API)."""
    results = []
    try:
        r = requests.get("https://remotive.com/api/remote-jobs", headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        data = r.json()
        for j in data.get("jobs", []):
            title = j.get("title", "")
            company = j.get("company_name", "")
            location = j.get("candidate_required_location", "Remote") or "Remote"
            url = j.get("url", "")
            if ok_title(title):
                results.append({
                    "company": company, "title": title, "location": location,
                    "url": url, "source": "remotive",
                })
    except Exception:
        pass
    return results


def search_weworkremotely():
    """Search We Work Remotely."""
    results = []
    urls = [
        "https://weworkremotely.com/categories/remote-back-end-programming-jobs",
        "https://weworkremotely.com/categories/remote-dev-sysadmin-jobs",
        "https://weworkremotely.com/categories/remote-product-jobs",
    ]
    for page_url in urls:
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                continue
            text = r.text
            # WWR uses <section> blocks with <li> job cards
            for m in re.finditer(
                r'<a\b[^>]*href="(/remote-jobs/[^"]+)"[^>]*>.*?<span class="title">(.*?)</span>.*?<span class="company">(.*?)</span>',
                text, re.I | re.S
            ):
                path = m.group(1)
                title = clean(m.group(2))
                company = clean(m.group(3))
                url = "https://weworkremotely.com" + path
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": "Remote",
                        "url": url, "source": "weworkremotely",
                    })
            # Fallback: broader pattern
            if not any(r2["source"] == "weworkremotely" for r2 in results):
                for m in re.finditer(r'href="(/remote-jobs/[^"]+)"[^>]*>(.*?)</a>', text, re.I | re.S):
                    label = clean(m.group(2))
                    if ok_title(label):
                        results.append({
                            "company": "We Work Remotely", "title": label, "location": "Remote",
                            "url": "https://weworkremotely.com" + m.group(1), "source": "weworkremotely",
                        })
        except Exception:
            continue
    return results


def search_builtin(queries):
    """Search Builtin."""
    results = []
    for query in queries:
        url = f"https://builtin.com/jobs?search={query.replace(' ', '+')}&remote=true"
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                continue
            text = r.text
            # Builtin uses Next.js, look for JSON in __NEXT_DATA__
            next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, re.S)
            if next_data:
                try:
                    data = json.loads(next_data.group(1))
                    # Navigate to job listings
                    props = data.get("props", {}).get("pageProps", {})
                    jobs = props.get("jobs", props.get("listings", []))
                    for j in jobs:
                        title = j.get("title", "")
                        company = j.get("company", j.get("companyName", ""))
                        location = j.get("location", j.get("locations", "Unlisted"))
                        link = j.get("url", j.get("applyUrl", ""))
                        if ok_title(title):
                            results.append({
                                "company": company, "title": title, "location": location,
                                "url": link, "source": "builtin",
                            })
                except json.JSONDecodeError:
                    pass
            # Fallback: regex
            for m in re.finditer(
                r'"title"\s*:\s*"(.*?)".*?"company(?:Name)?"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)"',
                text, re.S
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": location,
                        "url": "", "source": "builtin",
                    })
        except Exception:
            continue
    return results


def search_hackernews():
    """Search HackerNews Who's Hiring (monthly thread)."""
    results = []
    try:
        r = requests.get("https://hacker-news.firebaseio.com/v0/askstories.json", headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        story_ids = r.json()[:30]
        for sid in story_ids:
            sr = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", headers=HEADERS, timeout=10)
            if sr.status_code != 200:
                continue
            story = sr.json()
            title = (story.get("title") or "").lower()
            if "who is hiring" not in title:
                continue
            # Found the thread
            kids = story.get("kids", [])[:80]
            for kid in kids:
                try:
                    cr = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{kid}.json", headers=HEADERS, timeout=10)
                    if cr.status_code != 200:
                        continue
                    comment = cr.json()
                    text = comment.get("text", "")
                    # Strip HTML
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = re.sub(r'&amp;', '&', text)
                    text = re.sub(r'&lt;', '<', text)
                    text = re.sub(r'&gt;', '>', text)
                    text = re.sub(r'&nbsp;', ' ', text)
                    # Parse: first line usually "Company | Title | Location | ..."
                    lines = text.strip().split('\n')
                    first_line = lines[0] if lines else ""
                    parts = [p.strip() for p in first_line.split('|')]
                    if len(parts) >= 2:
                        company = parts[0][:60]
                        role = parts[1][:120]
                        location = parts[2][:60] if len(parts) > 2 else "See posting"
                        if ok_title(role):
                            results.append({
                                "company": company, "title": role, "location": location,
                                "url": f"https://news.ycombinator.com/item?id={kid}",
                                "source": "hackernews",
                            })
                except Exception:
                    continue
            break
    except Exception:
        pass
    return results


def search_jooble(queries):
    """Search Jooble (may need Byparr)."""
    results = []
    for query in queries:
        url = f"https://jooble.org/SearchResult?ukw={query.replace(' ', '+')}&loc=United+States"
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                continue
            for m in re.finditer(
                r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)".*?"link"\s*:\s*"(.*?)"',
                r.text, re.S
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                link = m.group(4).replace("\\/", "/")
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": location,
                        "url": link if link.startswith("http") else "", "source": "jooble",
                    })
        except Exception:
            continue
    return results


def search_adzuna(queries):
    """Search Adzuna."""
    results = []
    for query in queries:
        url = f"https://www.adzuna.com/search?query={query.replace(' ', '+')}&loc=us"
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                continue
            for m in re.finditer(
                r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*{[^}]*"display_name"\s*:\s*"(.*?)".*?"location"\s*:\s*{[^}]*"area"\s*:\s*\[(.*?)\]',
                r.text, re.S
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3).split(',')[-1].strip('" ')) if m.group(3) else "Unlisted"
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": location,
                        "url": "", "source": "adzuna",
                    })
        except Exception:
            continue
    return results


def search_talentcom(queries):
    """Search Talent.com."""
    results = []
    for query in queries:
        url = f"https://www.talent.com/jobs?k={query.replace(' ', '+')}&l=United+States"
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                continue
            for m in re.finditer(
                r'"jobTitle"\s*:\s*"(.*?)".*?"companyName"\s*:\s*"(.*?)".*?"jobLocation"\s*:\s*"(.*?)"',
                r.text, re.S
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": location,
                        "url": "", "source": "talent.com",
                    })
        except Exception:
            continue
    return results


def search_linkup():
    """Search LinkUp (indexes directly from company sites)."""
    results = []
    try:
        url = "https://www.linkup.com/job-search/it-manager"
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        for m in re.finditer(
            r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)".*?"url"\s*:\s*"(.*?)"',
            r.text, re.S
        ):
            title = clean(m.group(1))
            company = clean(m.group(2))
            location = clean(m.group(3))
            link = m.group(4).replace("\\/", "/")
            if ok_title(title):
                results.append({
                    "company": company, "title": title, "location": location,
                    "url": link, "source": "linkup",
                })
    except Exception:
        pass
    return results


def search_getwork():
    """Search Getwork (pulls from employer career pages)."""
    results = []
    try:
        url = "https://getwork.com/search?q=IT+Manager&l=United+States"
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        for m in re.finditer(
            r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)"',
            r.text, re.S
        ):
            title = clean(m.group(1))
            company = clean(m.group(2))
            location = clean(m.group(3))
            if ok_title(title):
                results.append({
                    "company": company, "title": title, "location": location,
                    "url": "", "source": "getwork",
                })
    except Exception:
        pass
    return results


def search_cybersecjobs():
    """Search CyberSecJobs."""
    results = []
    try:
        url = "https://www.cybersecjobs.com/search?q=IT+Manager"
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        for m in re.finditer(
            r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)"',
            r.text, re.S
        ):
            title = clean(m.group(1))
            company = clean(m.group(2))
            location = clean(m.group(3))
            if ok_title(title):
                results.append({
                    "company": company, "title": title, "location": location,
                    "url": "", "source": "cybersecjobs",
                })
    except Exception:
        pass
    return results


def search_theladders_api():
    """Search The Ladders via API (no browser needed)."""
    results = []
    try:
        url = "https://www.theladders.com/api/jobs?keywords=IT+Manager&location=&page=1&pageSize=25"
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        data = r.json()
        for j in data.get("jobs", data.get("results", [])):
            title = j.get("title", "")
            company = j.get("company", j.get("companyName", ""))
            location = j.get("location", "Unlisted")
            link = j.get("url", j.get("jobUrl", ""))
            if ok_title(title):
                results.append({
                    "company": company, "title": title, "location": location,
                    "url": link, "source": "theladders",
                })
    except Exception:
        pass
    return results


def search_governmentjobs():
    """Search GovernmentJobs (NEOGOV)."""
    results = []
    try:
        url = "https://www.governmentjobs.com/careers?keywords=IT+Manager&location=Las+Vegas%2C+NV"
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        for m in re.finditer(
            r'"title"\s*:\s*"(.*?)".*?"agency"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)"',
            r.text, re.S
        ):
            title = clean(m.group(1))
            company = clean(m.group(2))
            location = clean(m.group(3))
            if ok_title(title):
                results.append({
                    "company": f"Gov: {company}", "title": title, "location": location,
                    "url": "", "source": "governmentjobs",
                })
    except Exception:
        pass
    return results


def search_clearancejobs():
    """Search ClearanceJobs (security clearance roles)."""
    results = []
    try:
        url = "https://www.clearancejobs.com/jobs?keyword=IT+Manager"
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return results
        for m in re.finditer(
            r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)"',
            r.text, re.S
        ):
            title = clean(m.group(1))
            company = clean(m.group(2))
            location = clean(m.group(3))
            if ok_title(title):
                results.append({
                    "company": company, "title": title, "location": location,
                    "url": "", "source": "clearancejobs",
                })
    except Exception:
        pass
    return results


# All direct board search functions
DIRECT_BOARDS = [
    ("dice", lambda: search_dice(["IT Manager", "IT Director", "Senior IT Manager", "IT Operations Manager", "Infrastructure Manager", "IT Manager Las Vegas"])),
    ("remoteok", search_remoteok),
    ("remotive", search_remotive),
    ("weworkremotely", search_weworkremotely),
    ("builtin", lambda: search_builtin(["IT Manager", "IT Director", "Infrastructure Manager"])),
    ("hackernews", search_hackernews),
    ("jooble", lambda: search_jooble(["IT Manager", "IT Director"])),
    ("adzuna", lambda: search_adzuna(["IT Manager", "IT Director"])),
    ("talent.com", lambda: search_talentcom(["IT Manager", "IT Director"])),
    ("linkup", search_linkup),
    ("getwork", search_getwork),
    ("theladders", search_theladders_api),
    ("governmentjobs", search_governmentjobs),
    ("clearancejobs", search_clearancejobs),
]


def scan_direct_boards():
    """Scan all direct-request boards."""
    all_results = []
    all_errors = []

    for name, fn in DIRECT_BOARDS:
        try:
            results = fn()
            all_results.extend(results)
        except Exception as e:
            all_errors.append(f"{name}: {e}")

    return all_results, all_errors
