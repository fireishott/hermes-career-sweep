"""Glassdoor scraping via requests. Falls back gracefully if blocked."""

import re
import requests
from sources.ats import clean, ok_title

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def search_glassdoor(queries):
    """Search Glassdoor for job listings. Returns list of job dicts."""
    results = []
    for query in queries:
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query.replace(' ', '+')}&locT=&locId=&locKeyword=&jobType=all&fromAge=7&radius=0"
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                continue
            # Parse job cards from HTML
            text = r.text
            # Glassdoor uses data-test attributes for job cards
            for m in re.finditer(
                r'"jobTitle":"(.*?)".*?"employerName":"(.*?)".*?"location":"(.*?)".*?"jobLink":"(.*?)"',
                text,
                re.S,
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                link = m.group(4).replace("\\/", "/")
                if not link.startswith("http"):
                    link = "https://www.glassdoor.com" + link
                if ok_title(title):
                    results.append({
                        "company": company,
                        "title": title,
                        "location": location,
                        "url": link,
                        "source": "glassdoor",
                    })
        except Exception:
            continue
    return results
