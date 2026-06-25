# Hermes Career Sweep

Job search automation — parallel ATS APIs + board scraping with intelligent filtering, scoring, and email delivery.

Configurable roles, scoring logic, and sources. Run it as-is for IT Manager focus, or customize it for any role (data engineer, product manager, SRE, etc.).

Built on [`career-ops`](https://github.com/santifer/career-ops) upstream. Credits in [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md).

---

## What It Does

- **ATS API scan** — 31+ company career pages via Greenhouse, Ashby, Lever, Workday APIs (11 seconds, zero LLM cost)
- **Board scraping** — 45+ job boards via `web_extract` (Dice, Indeed, Glassdoor, LinkedIn, remote specialists, local employers, government, etc.)
- **Smart title filtering** — two-part: exact phrases (e.g., "Data Engineer") + leadership+domain combos (e.g., "Senior Manager, Data")
- **Location filtering** — US-only default, Vegas bonus, remote US bonus (fully configurable)
- **Intelligent scoring** — role-based points + location bonuses + company tier bonuses
- **Deduplication** — tracks applied companies, avoids re-scanning

**Output:** Ranked list of jobs grouped by fit (HIGH/MEDIUM/LOW), emailed as formatted table with direct apply links.

---

## Quick Start

### Default Config: IT Manager / Sr IT Manager

```bash
cd /home/fihadmin/career-sweep
python3 sweep.py scan --json
```

Returns: 1-6 jobs from 31 ATS companies in ~11 seconds.

### Customize for Your Role

Edit `config.py`:

```python
# Change these to match YOUR target role
EXACT_PHRASES = [
    "data engineer", "sr data engineer", "senior data engineer",
    "data engineering manager",
]

LEADERSHIP_TERMS = ["senior engineer", "sr engineer", "manager"]
DOMAIN_TERMS = ["data", "analytics", "data platform"]

TITLE_SCORES = {
    "data engineer": 8,
    "senior data engineer": 9,
    "data engineering manager": 9,
}

# Adjust location bonuses
VEGAS_BONUS = 0  # Don't care about Vegas
REMOTE_BONUS = 5  # Heavily prefer remote

# Add ATS companies relevant to your role
ATS_COMPANIES = [
    ("Databricks", "greenhouse", "databricks"),
    ("Stripe", "greenhouse", "stripe"),
    # ... customize
]
```

Then run: `python3 sweep.py scan --json`

---

## Architecture

```
┌────────────────────────────────────┐
│       Python ATS Scan              │
│  31+ companies, 11s, 1-6 jobs      │
└──────────┬───────────────────────────┘
           │
    ┌──────▼──────┐
    │   Cron      │
    │   6am/1pm   │
    │   PT daily  │
    │   Agent     │
    │  scrapes    │
    │   45+       │
    │   boards    │
    └──────┬──────┘
           │
    ┌──────▼──────────┐
    │  Dedupe         │
    │  Score          │
    │  Filter by      │
    │  location +     │
    │  title rules    │
    └──────┬──────────┘
           │
    ┌──────▼──────┐
    │  Email      │
    │  Report     │
    │  (SMTP)     │
    └─────────────┘
```

### Step 1: ATS API Scan

Hits 31 configured ATS companies via their public APIs:

- **Greenhouse** — Anthropic, OpenAI, Stripe, Cloudflare, Datadog, Snowflake, Airtable, Samsara, Twilio, etc.
- **Ashby** — Figma, Vercel, Databricks, etc.
- **Lever** — Retool, Tinybird, etc.
- **Workday** — Salesforce, Genesys, etc.
- **Direct** — MGM Resorts, Caesars, Station Casinos, etc.

**Output:** Jobs matching your role filter, scored.

### Step 2: Board Scraping (Cron Agent)

Nine batches of `web_extract` across 45+ boards. Organized by category:

| Category | Boards |
|---|---|
| **Mega Aggregators** | Indeed, Glassdoor, LinkedIn, ZipRecruiter, Monster, CareerBuilder, Jooble, Adzuna, Talent.com |
| **Tech/Specialized** | Dice, Builtin, Wellfound, Cybersecurity Jobs, AI-Jobs |
| **Remote** | WeWorkRemotely, RemoteOK, Remotive, Remote.co, Virtual Vocations, Jobspresso, JustRemote, FlexJobs |
| **Executive** | The Ladders, IvyExec, 6FigureJobs |
| **Local (Vegas)** | MGM, Caesars, Wynn, Station Casinos, Clark County, City of Las Vegas |
| **Government** | USAJobs, GovernmentJobs, Nevada JobConnect |
| **Startup** | Wellfound, WorkAtAStartup |
| **Other** | LinkUp, Getwork, HiringCafe, ClearanceJobs, NoDesk, Pangian, Braintrust |

Agent parses job titles, filters by your role rules, and saves results to JSON.

### Step 3: Dedupe + Score + Email

- **Deduplicate** on company + title
- **Score** based on role fit + location bonuses + company tier
- **Label** as HIGH (15+), MEDIUM (8-14), LOW (<8)
- **Email** formatted report with direct apply links

---

## Configuration

All behavior is driven by `config.py`. Customize:

### Target Roles

```python
EXACT_PHRASES = [
    "role title 1", "role title 2", "role title 3",
]

LEADERSHIP_TERMS = ["manager", "senior engineer", "lead"]
DOMAIN_TERMS = ["domain", "platform", "ops"]

TITLE_NEGATIVES = [
    "director", "vp", "chief",  # Reject these
]
```

### Scoring

```python
SCORING = {
    "remote_bonus": 3,           # +3 for remote
    "vegas_bonus": 5,            # +5 for Las Vegas
    "top_company_bonus": 3,      # +3 for top companies
}

TITLE_SCORES = {
    "exact match role": 9,
    "related role": 8,
    "broader role": 5,
}
```

### ATS Companies

```python
ATS_COMPANIES = [
    ("Company Name", "greenhouse", "ats-slug"),
    ("Company Name", "ashby", "ats-slug"),
    # Add or remove companies
]
```

### Location Rules

```python
LOCATION_FILTER = {
    "accept_remote": True,
    "accept_vegas": True,
    "accept_us_cities": True,
    "reject_international_only": True,
}
```

### Email

Set via environment variables or `config.py`:

```python
EMAIL_FROM = os.getenv("EMAIL_FROM")        # Your SMTP login email
EMAIL_TO = os.getenv("EMAIL_TO")            # Recipient email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mail.me.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")          # Same as EMAIL_FROM usually
SMTP_PASS = os.getenv("SMTP_PASS")          # App-specific password, NOT your account password
```

Do NOT commit email addresses or passwords to git. Use environment variables.

---

## Usage

### ATS Scan Only

```bash
cd /home/fihadmin/career-sweep
python3 sweep.py scan --json
```

Fast, no network. Returns JSON with company, title, location, URL, score.

### Full Sweep (ATS + Board Scraping)

Triggered daily by cron at 6am/1pm PT:

```bash
0 6,13 * * *  cd /home/fihadmin/career-sweep && python3 sweep.py scan --json && \
              hermes agent prompt "Scrape 45+ boards, parse, merge, email"
```

Agent:
1. Runs ATS scan
2. Scrapes all board URLs via web_extract (9 batches)
3. Merges results
4. Dedupes by company+title
5. Scores and ranks
6. Emails report

### Manual Run

```bash
# Just scan ATS
python3 sweep.py scan --json > /tmp/ats.json

# Manually trigger board scrape (or wait for cron)
# Then merge and email:
python3 sweep.py merge \
  --ats-results /tmp/ats.json \
  --board-results data/board-results-YYYY-MM-DD.json
```

---

## Results

### Output Format

Email arrives as formatted table:

```
Career Sweep Morning - 2026-06-25
Run at 08:49 AM PT

Total: 4 | HIGH: 0 | MEDIUM: 4 | LOW: 0
Las Vegas: 1 | Remote US: 0
Raw jobs processed: 16

============================================================

MEDIUM PRIORITY (8-14)
----------------------------------------
  Company Name
    Job Title
    Location
    https://apply-link.com
    Score: 9/25 | source
```

Grouped by tier (HIGH, MEDIUM, LOW), sorted by score.

---

## File Structure

```
/home/fihadmin/career-sweep/
├── sweep.py              # Main CLI: scan, merge, email
├── config.py             # YOUR CUSTOMIZATION: roles, scoring, ATS, email
├── pipeline.py           # Dedupe, rank, seen tracking, email helper
├── mail.py               # Email formatting and SMTP
├── sources/
│   ├── utils.py          # ok_title(), score_title(), clean()
│   ├── ats.py            # ATS API queries
│   ├── byparr.py         # Byparr integration (optional)
│   ├── camofox.py        # CamoFox integration (optional)
│   ├── nodriver.py       # nodriver browser (optional)
│   └── direct.py         # Direct HTTP requests
├── data/
│   ├── seen.json         # Tracked (company, title) pairs
│   ├── applied.json      # Companies you've applied to
│   ├── ats-*.json        # ATS results
│   ├── board-results-*.json  # Board scrape results
│   └── sweep-*.txt       # Email reports
├── README.md             # This file
├── CLAUDE.md             # Implementation guide
└── .gitignore
```

---

## Customization Examples

### Example 1: Data Engineer Focus

```python
# config.py
EXACT_PHRASES = [
    "data engineer", "sr data engineer", "senior data engineer",
]

LEADERSHIP_TERMS = ["manager", "lead", "principal"]
DOMAIN_TERMS = ["data", "analytics", "engineering"]

TITLE_SCORES = {
    "data engineer": 8,
    "senior data engineer": 9,
    "data engineering manager": 9,
    "data platform engineer": 8,
}

ATS_COMPANIES = [
    ("Databricks", "greenhouse", "databricks"),
    ("Stripe", "greenhouse", "stripe"),
    ("Figma", "ashby", "figma"),
    ("Retool", "lever", "retool"),
]
```

Run: `python3 sweep.py scan --json`

### Example 2: Remote-First, No Vegas Preference

```python
# config.py
VEGAS_BONUS = 0        # Don't care
REMOTE_BONUS = 5       # Heavily prefer
TOP_COMPANY_BONUS = 1  # Ignore company tier

LOCATION_FILTER = {
    "accept_remote": True,
    "reject_us_cities_onsite": True,  # Only remote
    "reject_vegas": False,             # But include Vegas if remote
}
```

### Example 3: Executive Search (Director+)

```python
# config.py
EXACT_PHRASES = [
    "director of engineering", "head of engineering",
    "vp of product", "chief product officer",
]

LEADERSHIP_TERMS = ["director", "vp", "chief", "head of"]
DOMAIN_TERMS = ["engineering", "product", "operations"]

TITLE_NEGATIVES = []  # Remove this — we DO want "director"

TITLE_SCORES = {
    "director of engineering": 10,
    "vp of product": 10,
    "chief product officer": 10,
}
```

---

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md). To customize for your role: edit `config.py` and commit to your fork.

---

## License

MIT. See [`LICENSE`](./LICENSE) or upstream [`CAREER_OPS_README.md`](./CAREER_OPS_README.md).

---

## Upstream Credit

Extends [`career-ops`](https://github.com/santifer/career-ops) by santifer.

See [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md) for full credits.
