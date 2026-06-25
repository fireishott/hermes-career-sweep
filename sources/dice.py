"""Dice scraping. Dice has a public search that returns structured data."""

import re
import requests
from sources.ats import clean, ok_title

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}


def search_dice(queries):
    """Search Dice for job listings. Returns list of job dicts."""
    results = []
    for query in queries:
        url = f"https://www.dice.com/jobs?q={query.replace(' ', '+')}&radius=30&radiusUnit=mi&page=1&pageSize=20&language=en"
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                continue
            text = r.text
            # Dice renders job cards with data attributes
            for m in re.finditer(
                r'"title":"(.*?)".*?"company":"(.*?)".*?"location":"(.*?)".*?"jobUrl":"(.*?)"',
                text,
                re.S,
            ):
                title = clean(m.group(1))
                company = clean(m.group(2))
                location = clean(m.group(3))
                link = m.group(4).replace("\\/", "/")
                if not link.startswith("http"):
                    link = "https://www.dice.com" + link
                if ok_title(title):
                    results.append({
                        "company": company,
                        "title": title,
                        "location": location,
                        "url": link,
                        "source": "dice",
                    })
        except Exception:
            continue
    return results
