"""nodriver source - lightweight browser fetch for pages that need JS rendering."""

import re
import json
import requests
from sources.utils import clean, ok_title

NODRIVER_URL = "http://127.0.0.1:8901/fetch"
NODRIVER_TIMEOUT = 45  # seconds


def nodriver_fetch(url, wait=3, bypass_cloudflare=False):
    """Fetch a page through nodriver browser."""
    r = requests.post(
        NODRIVER_URL,
        json={"url": url, "wait_seconds": wait, "bypass_cloudflare": bypass_cloudflare},
        timeout=NODRIVER_TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        return None
    return data.get("html", "")


def extract_jobs_from_html(html_text, company_name, source="nodriver"):
    """Extract job listings from HTML using title matching."""
    results = []
    if not html_text:
        return results

    # Strip tags for text matching
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    # Look for job title patterns
    for kw in ["manager", "director", "head", "infrastructure", "operations"]:
        for m in re.finditer(
            r'([^\n.]{0,80}' + re.escape(kw) + r'[^\n.]{0,80})',
            text, re.I
        ):
            context = m.group(1).strip()
            if ok_title(context):
                results.append({
                    "company": company_name,
                    "title": context[:120],
                    "location": "Unlisted",
                    "url": "",
                    "source": source,
                })

    # Also try structured data extraction
    for m in re.finditer(
        r'"title"\s*:\s*"(.*?)".*?"company(?:Name)?"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)"',
        html_text, re.S
    ):
        title = clean(m.group(1))
        company = clean(m.group(2))
        location = clean(m.group(3))
        if ok_title(title):
            results.append({
                "company": company or company_name, "title": title, "location": location,
                "url": "", "source": source,
            })

    # Try link-based extraction
    for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text, re.I | re.S):
        href = m.group(1)
        label = clean(re.sub(r'<[^>]+>', ' ', m.group(2)))
        if label and 10 < len(label) < 200 and ok_title(label):
            results.append({
                "company": company_name, "title": label, "location": "Unlisted",
                "url": href if href.startswith("http") else "",
                "source": source,
            })

    return results


def search_career_page(url, company_name):
    """Scrape a career page via nodriver."""
    try:
        html = nodriver_fetch(url, wait=5)
        return extract_jobs_from_html(html, company_name, f"nodriver:{company_name}")
    except Exception:
        return []


def search_dice_nodriver(queries):
    """Search Dice via nodriver (bypasses anti-bot)."""
    results = []
    for query in queries:
        url = f"https://www.dice.com/jobs?q={query.replace(' ', '+')}&radius=30&radiusUnit=mi&page=1&pageSize=20"
        try:
            html = nodriver_fetch(url, wait=5)
            if not html:
                continue
            # Parse job cards
            for m in re.finditer(
                r'"title"\s*:\s*"(.*?)".*?"company"\s*:\s*"(.*?)".*?"location"\s*:\s*"(.*?)"',
                html, re.S
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                if ok_title(title):
                    results.append({
                        "company": company, "title": title, "location": location,
                        "url": "", "source": "nodriver:dice",
                    })
        except Exception:
            continue
    return results


def search_ziprecruiter_nodriver(queries):
    """Search ZipRecruiter via nodriver."""
    results = []
    for query in queries:
        url = f"https://www.ziprecruiter.com/jobs-search?search={query.replace(' ', '+')}&location="
        try:
            html = nodriver_fetch(url, wait=5)
            results.extend(extract_jobs_from_html(html, "ZipRecruiter", "nodriver:ziprecruiter"))
        except Exception:
            continue
    return results


def search_wellfound_nodriver():
    """Search Wellfound (AngelList) via nodriver."""
    results = []
    try:
        html = nodriver_fetch("https://wellfound.com/role/r/it-manager", wait=5)
        results.extend(extract_jobs_from_html(html, "Wellfound", "nodriver:wellfound"))
    except Exception:
        pass
    return results


# Career pages - full master list, runs in parallel so speed is fine
NODRIVER_CAREER_PAGES = [
    # Vegas local (highest priority)
    ("https://careers.mgmresorts.com", "MGM Resorts"),
    ("https://careers.caesars.com", "Caesars Entertainment"),
    ("https://careers.wynnresorts.com", "Wynn Resorts"),
    ("https://www.stationcasinos.com/careers", "Station Casinos"),
    ("https://www.clarkcountynv.gov/government/departments/human_resources/employment.php", "Clark County"),
    ("https://www.lasvegasnevada.gov/Government/Departments/Human-Resources/Employment", "City of Las Vegas"),
    # Federal/State
    ("https://www.usajobs.gov", "USAJobs"),
    ("https://www.governmentjobs.com/careers?keywords=IT+Manager&location=Las+Vegas", "GovernmentJobs"),
    ("https://www.nevadajobconnect.com", "Nevada JobConnect"),
    # Tech giants
    ("https://careers.google.com", "Google"),
    ("https://www.metacareers.com", "Meta"),
    ("https://careers.apple.com", "Apple"),
    ("https://www.amazon.jobs", "Amazon"),
    ("https://careers.microsoft.com", "Microsoft"),
    ("https://www.salesforce.com/company/careers", "Salesforce"),
    # High-paying remote specialists
    ("https://weworkremotely.com", "We Work Remotely"),
    ("https://remote.co", "Remote.co"),
    ("https://www.virtualvocations.com", "Virtual Vocations"),
    ("https://www.workingnomads.com", "Working Nomads"),
    ("https://jobspresso.co", "Jobspresso"),
    ("https://justremote.co", "JustRemote"),
    ("https://remoterocketship.com", "Remote Rocketship"),
    ("https://nodesk.co", "NoDesk"),
    # Executive
    ("https://www.theladders.com", "The Ladders"),
    ("https://www.ivyexec.com", "Ivy Exec"),
    ("https://www.6figurejobs.com", "6FigureJobs"),
    # AI/ML niche
    ("https://ai-jobs.net", "AI-Jobs.net"),
    ("https://mljobs.io", "MLJobs.io"),
    # Startup
    ("https://wellfound.com", "Wellfound"),
    ("https://www.workatastartup.com", "YC Startup"),
    ("https://startup.jobs", "Startup Jobs"),
    # Aggregators
    ("https://jooble.org", "Jooble"),
    ("https://www.adzuna.com", "Adzuna"),
    ("https://www.talent.com", "Talent.com"),
    ("https://www.linkup.com", "LinkUp"),
    ("https://getwork.com", "Getwork"),
    ("https://hiring.cafe", "HiringCafe"),
    # Other
    ("https://www.cybersecjobs.com", "CyberSecJobs"),
    ("https://www.clearancejobs.com", "ClearanceJobs"),
    ("https://builtin.com", "Builtin"),
    ("https://remoteok.com", "RemoteOK"),
    ("https://remotive.com", "Remotive"),
]

NODRIVER_DICE_QUERIES = [
    "IT Manager",
    "IT Director",
    "Senior IT Manager",
    "IT Operations Manager",
    "Infrastructure Manager",
    "IT Manager Las Vegas",
]


def scan_nodriver_boards():
    """Scan boards via nodriver browser fetch."""
    all_results = []
    all_errors = []

    # Dice via nodriver
    try:
        results = search_dice_nodriver(NODRIVER_DICE_QUERIES)
        all_results.extend(results)
    except Exception as e:
        all_errors.append(f"nodriver:dice: {e}")

    # Career pages
    for url, company in NODRIVER_CAREER_PAGES:
        try:
            results = search_career_page(url, company)
            all_results.extend(results)
        except Exception as e:
            all_errors.append(f"nodriver:{company}: {e}")

    return all_results, all_errors
