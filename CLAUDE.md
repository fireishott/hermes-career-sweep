# Hermes Career Sweep v2.0 — Implementation Guide

Focused IT Manager and Sr IT Manager job search. Parallel ATS APIs + board scraping with stealth browsing.

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                    Python ATS Scan                          │
│  sweep.py scan --json → 31 companies, ~11s, 1-6 jobs       │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │   Cron Job      │
                │  6am/1pm PT     │
                │  Runs Agent     │
                │  web_extract    │
                │  45+ boards     │
                └────────┬────────┘
                         │
            ┌────────────┴────────────┐
            │   Dedupe + Score        │
            │   Location Filter       │
            │   seen.json tracking    │
            └────────────┬────────────┘
                         │
                  ┌──────▼──────┐
                  │   Email     │
                  │   SMTP      │
                  │   Report    │
                  └─────────────┘
```

---

## File Structure

```
/home/fihadmin/career-sweep/
├── sweep.py                 # Main orchestrator (ATS scan + merge pipeline)
├── config.py                # Roles, scoring, ATS companies, SMTP
├── pipeline.py              # Dedupe, rank, seen tracking, email helper
├── mail.py                  # format_report(), send_email()
├── sources/
│   ├── utils.py             # ok_title(), clean(), score_title()
│   ├── ats.py               # Greenhouse, Ashby, Lever, Workday APIs
│   ├── byparr.py            # Indeed, Glassdoor (via Byparr, port 8191)
│   ├── camofox.py           # LinkedIn auth (via CamoFox, port 9377)
│   ├── nodriver.py          # Career pages (via nodriver, port 8901)
│   └── direct.py            # HTTP requests (Dice, RemoteOK, etc.)
├── data/
│   ├── seen.json            # Company+title SHA256 hashes (avoid rescans)
│   ├── applied.json         # Companies already applied to
│   ├── ats-*.json           # ATS API results
│   ├── board-results-*.json # Web scrape results
│   ├── results-*.json       # Final merged, ranked jobs
│   └── sweep-*.txt          # Email report
├── README.md                # User-facing overview
├── CLAUDE.md                # This file
└── .gitignore               # data/ + __pycache__
```

---

## Key Modules

### `sweep.py`

**Main CLI:**

```bash
python3 sweep.py scan --json          # ATS APIs only
python3 sweep.py merge \
  --board-results data/board-results-*.json \
  --ats-results data/ats-*.json \
  --json                                # Merge, score, email
```

**Functions:**

- `run_ats_scan()` — hits 31 ATS companies, filters to IT Manager/Sr IT Manager, returns JSON
- `merge_and_email(board_jobs, ats_result)` — combines board + ATS results, dedupes, scores, emails
- Returns: `{status, elapsed_seconds, raw_matches, filtered, high/medium/low, jobs, errors}`

### `config.py`

**Roles:**

```python
EXACT_PHRASES = [
    "it manager", "sr it manager", "senior it manager",
    "it operations manager", "infrastructure manager",
]

LEADERSHIP_TERMS = ["senior manager", "sr manager", "manager"]
DOMAIN_TERMS = ["it", "infrastructure", "technology operations", "workplace technology"]
```

**Scoring:**

```python
SCORING = {
    "remote_bonus": 3,
    "vegas_bonus": 5,
    "top_company_bonus": 3,
}

TITLE_SCORES = {
    "senior it manager": 9,
    "sr it manager": 9,
    "it manager": 8,
    "it operations manager": 8,
    "infrastructure manager": 8,
}
```

**ATS Companies:**

```python
ATS_COMPANIES = [
    ("Anthropic", "greenhouse", "anthropic"),
    ("OpenAI", "greenhouse", "openai"),
    ("Stripe", "greenhouse", "stripe"),
    # ... 28 more
]
```

### `sources/utils.py`

**Core filter:**

```python
def ok_title(title):
    """Two-part title match: exact phrases OR leadership+domain combo."""
    title_lower = title.lower()
    
    # Exact phrase match
    if any(phrase in title_lower for phrase in EXACT_PHRASES):
        return True
    
    # Reject negatives first
    if any(neg in title_lower for neg in TITLE_NEGATIVES):
        return False
    
    # Leadership + domain combo
    has_leadership = any(term in title_lower for term in LEADERSHIP_TERMS)
    has_domain = any(term in title_lower for term in DOMAIN_TERMS)
    
    return has_leadership and has_domain

def score_title(title, company, location):
    """Assign score based on title, company, location."""
    # Base score from title
    score = TITLE_SCORES.get(title.lower(), 0)
    
    # Bonuses
    if "remote" in location.lower():
        score += SCORING["remote_bonus"]
    if "vegas" in location.lower() or "las vegas" in location.lower():
        score += SCORING["vegas_bonus"]
    if any(tc in company.lower() for tc in TOP_COMPANIES):
        score += SCORING["top_company_bonus"]
    
    return score
```

### `sources/ats.py`

Queries Greenhouse, Ashby, Lever, Workday APIs for career pages:

```python
def scan_ats_companies(companies):
    """Scan ATS APIs, return (jobs, errors)."""
    jobs = []
    errors = []
    
    for company_name, ats_type, slug in companies:
        try:
            if ats_type == "greenhouse":
                results = query_greenhouse(slug)
            elif ats_type == "ashby":
                results = query_ashby(slug)
            # ... etc
            
            # Filter & rank
            for job in results:
                if ok_title(job["title"]) and ok_location(job["location"]):
                    job["score"] = score_title(job["title"], company_name, job["location"])
                    jobs.append(job)
        except Exception as e:
            errors.append(f"{company_name}: {e}")
    
    return jobs, errors
```

### `pipeline.py`

**Dedupe:**

```python
def deduplicate(jobs):
    """Remove duplicate company+title combos."""
    seen = {}
    unique = []
    for job in jobs:
        key = (clean(job["company"]), clean(job["title"]))
        if key not in seen:
            seen[key] = True
            unique.append(job)
    return unique
```

**Rank:**

```python
def rank_jobs(jobs):
    """Assign labels, sort by score."""
    for job in jobs:
        score = job.get("score", 0)
        if score >= 15:
            job["label"] = "HIGH"
        elif score >= 8:
            job["label"] = "MEDIUM"
        else:
            job["label"] = "LOW"
    
    return sorted(jobs, key=lambda j: j.get("score", 0), reverse=True)
```

**Seen tracking:**

```python
def update_seen(jobs):
    """Add jobs to seen.json to avoid rescanning."""
    seen = load_json(SEEN_FILE, [])
    for job in jobs:
        key = hashlib.sha256(
            f"{job['company']}:{job['title']}".encode()
        ).hexdigest()
        if key not in seen:
            seen.append(key)
    save_json(SEEN_FILE, seen)
```

### `mail.py`

**Email formatting:**

```python
def format_report(jobs, errors=None, total_scanned=0, source_counts=None):
    """Generate formatted text report."""
    report = f"""Career Sweep Morning - {datetime.now().strftime('%Y-%m-%d')}
Run at {datetime.now().strftime('%I:%M %p %Z')}

Total: {len(jobs)} | HIGH: {len([j for j in jobs if j['label']=='HIGH'])} | MEDIUM: ... | LOW: ...
Las Vegas: {len([j for j in jobs if j['location_type']=='vegas'])} | Remote US: {len([j for j in jobs if j['location_type']=='remote_us'])}

...
"""
    return report

def send_email(subject, body):
    """Send via iCloud SMTP."""
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False
```

---

## Cron Job

**Schedule:** `0 6,13 * * *` (6am/1pm PT daily)

**Command:**

```bash
cd /home/fihadmin/career-sweep && python3 sweep.py scan --json > /tmp/ats.json && \
hermes agent prompt "
Run web_extract on 45+ job boards (see PROMPT in cron job definition).
Parse and save board results to /home/fihadmin/career-sweep/data/board-results-YYYY-MM-DD.json.
Merge with ATS results and send email.
"
```

**Agent prompt includes:**

- 9 batches of board URLs (Dice, Builtin, remote specialists, Vegas local, government, startup, etc.)
- Title parsing: "IT Manager" and "Sr IT Manager" only
- Location parsing: Remote US, Las Vegas, US cities only
- Output format: JSON with company, title, location, URL, source
- Merge and email via Python script

---

## Customization

### Change Target Roles

Edit `config.py`:

```python
EXACT_PHRASES = [
    "infrastructure engineer",
    "sr infrastructure engineer",
    "devops manager",
]

TITLE_SCORES = {
    "infrastructure engineer": 8,
    "sr infrastructure engineer": 9,
    "devops manager": 8,
}
```

### Change Scoring

```python
SCORING = {
    "remote_bonus": 5,  # ↑ prioritize remote
    "vegas_bonus": 2,   # ↓ less picky on Vegas
    "top_company_bonus": 1,  # ↓ less weight on company
}
```

### Add/Remove ATS Companies

```python
ATS_COMPANIES = [
    ("NewCompany", "greenhouse", "newcompany-slug"),
    # ...
]
```

### Change Email

```python
EMAIL_TO = "your-email@example.com"
SMTP_USER = "your-icloud@icloud.com"
SMTP_PASS = "your-app-password"
```

---

## Testing

### ATS Scan Only (Fast)

```bash
cd /home/fihadmin/career-sweep
python3 sweep.py scan --json
```

Expected: 1-6 jobs from 31 companies in ~11 seconds.

### Full E2E (requires agent web_extract)

Local testing not recommended (agent needed). Use cron job runs or manual agent dispatch.

### Title Filter

```python
python3 -c "
from sources.utils import ok_title
tests = [
    ('IT Manager', True),
    ('Sr IT Manager', True),
    ('Director of IT', False),
    ('VP of Infrastructure', False),
]
for title, expected in tests:
    result = ok_title(title)
    print(f'{title}: {result} [{\"✓\" if result == expected else \"✗\"}]')
"
```

---

## Troubleshooting

### ATS scan returns 0 jobs

Check:
1. Company slugs in `config.py` are correct
2. APIs are responding (test via curl)
3. Title filter is too strict (run test above)

### Email not sending

Check:
1. iCloud SMTP credentials in `config.py`
2. SMTP_PASS is app-specific password (not iCloud password)
3. `mail.py`: `send_email()` error logs

### Board scraping missing jobs

Check:
1. web_extract is reaching the URLs
2. Job titles in results match the role filter (test with `ok_title()`)
3. Location filter is not removing valid US locations

---

## Data Contract

**User-customizable (edit these):**
- `config.py` — roles, scoring, SMTP, ATS companies
- `data/seen.json` — can be reset with `rm -f data/seen.json`

**System files (don't modify):**
- `sweep.py`, `pipeline.py`, `mail.py`, `sources/*` — updated from repo
- `.gitignore`, `README.md`, `CLAUDE.md` — documentation

---

## Upstream Credit

Extends [`career-ops`](https://github.com/santifer/career-ops) by santifer.

See [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md).
