# Hermes Career Sweep v2.0

Focused IT Manager and Sr IT Manager job sweep. Parallel sources (ATS APIs + board scraping) with stealth browsing, intelligent filtering, and email delivery.

Built on [`career-ops`](https://github.com/santifer/career-ops) upstream. Credits in [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md).

---

## What's New (v2.0)

- **Narrow focus** — IT Manager and Sr IT Manager only (no Directors, VPs, engineering managers)
- **Two-part title filter** — exact phrases (e.g., "IT Manager") + leadership+domain combos (e.g., "Senior Manager, IT Operations")
- **ATS API scan** — 31 companies via Greenhouse, Ashby, Lever, Workday (11 seconds, zero LLM overhead)
- **Stealth modules** — Byparr (Indeed/Glassdoor bypass), CamoFox (LinkedIn auth), nodriver (career pages), direct requests
- **Smart scoring** — Sr IT Manager=9, IT Manager=8, Vegas=+5, Remote=+3, Top Tech Co=+3
- **Location filter** — US-only (Remote US, Las Vegas, US cities). Rejects international-only listings
- **Email delivery** — iCloud SMTP, formatted table, HIGH/MEDIUM/LOW tiers
- **Cron schedule** — 6am/1pm PT daily
- **Dedup tracking** — seen.json and applied.json prevent re-scanning

---

## Architecture

```
┌────────────────────────────────────┐
│       Python ATS API Scan          │
│  (31 companies, 11s, 1-6 jobs)     │
└──────────────┬─────────────────────┘
               │
         ┌─────▼──────┐
         │  Agent     │
         │ web_extract
         │ (45+ boards)
         │  ~2 min    │
         └─────┬──────┘
               │
      ┌────────▼─────────┐
      │  Dedupe + Score  │
      │  Location Filter │
      └────────┬─────────┘
               │
         ┌─────▼──────┐
         │    Email   │
         │  iCloud    │
         │    SMTP    │
         └────────────┘
```

### Step 1: ATS API Scan

- Greenhouse (Anthropic, OpenAI, Stripe, Cloudflare, Datadog, Snowflake, Airtable, Samsara, Twilio, etc.)
- Ashby (Figma, Vercel, Databricks, etc.)
- Lever (Retool, Tinybird, etc.)
- Workday (Salesforce, Genesys)
- Plus dedicated scrapers: MGM Resorts, Caesars, Station Casinos

**Output:** 10-15 raw matches, filtered to 1-6 by role.

### Step 2: Board Scraping (Agent-Driven)

Nine batches of `web_extract` across 45+ boards:

- **Mega Aggregators** — Indeed, Glassdoor, ZipRecruiter, Monster, CareerBuilder, Jooble, Adzuna, Talent.com, LinkedIn
- **Dice & Tech** — Dice, Builtin, Wellfound, Cybersecurity Jobs, AI-Jobs.net
- **Remote Specialists** — WeWorkRemotely, RemoteOK, Remotive, Remote.co, Virtual Vocations, Working Nomads, Jobspresso, JustRemote, RemoteRocketship, FlexJobs
- **Executive** — The Ladders, IvyExec, 6FigureJobs
- **Vegas Local** — MGM, Caesars, Wynn, Station Casinos, Clark County, City of Las Vegas
- **Government** — USAJobs, GovernmentJobs, Nevada JobConnect
- **Startup** — Wellfound, WorkAtAStartup, Startup Jobs
- **Other** — Adzuna, Talent.com, LinkUp, Getwork, HiringCafe, ClearanceJobs, NoDesk, Pangian, Braintrust

### Step 3: Role Filter

**Must match one of:**

- Exact phrases: "IT Manager", "Sr IT Manager", "Senior IT Manager", "IT Operations Manager", "Infrastructure Manager"
- Leadership + domain: ("Senior Manager" OR "Sr Manager" OR "Manager") + ("IT" OR "Infrastructure" OR "Technology Operations")

**Rejected:** Directors, VPs, engineering managers, product managers, campaign managers, recruiting, sales, marketing, data science, nurses, bartenders, etc.

### Step 4: Location Filter

**Accepted:**
- "Remote US", "Remote, US", "Anywhere", "Work from home"
- Las Vegas, Reno, Henderson, North Las Vegas (Nevada only)
- US cities (New York, Boston, Seattle, SF, LA, Chicago, Austin, Denver, etc.)

**Rejected:**
- International-only (UK-only, Germany-only, Canada only, etc.)
- No location specified

### Step 5: Dedup & Score

- **Deduplicate** on company + title (case-insensitive)
- **Score:** base + bonuses
  - Sr IT Manager: 9
  - IT Manager: 8
  - IT Operations Manager: 8
  - Infrastructure Manager: 8
  - Las Vegas: +5
  - Remote US: +3
  - Top Tech Co (Google, Meta, Apple, etc.): +3
- **Labels:** HIGH (15+), MEDIUM (8-14), LOW (<8)

### Step 6: Email Report

Formatted text report emailed to `freemancurtisd@gmail.com` via `fihassistant@icloud.com`:

```
Career Sweep Morning - 2026-06-25
Run at 08:49 AM PT

Total: 4 | HIGH: 0 | MEDIUM: 4 | LOW: 0
Las Vegas: 1 | Remote US: 0
Raw jobs processed: 16
Sources: ats: 1 | boards: 15

============================================================

MEDIUM PRIORITY (8-14)
----------------------------------------
  Lendbuzz
    Senior Manager, IT Systems
    Boston, MA
    https://www.dice.com/job-detail/5d5005d3-61ac-4744-9d2d-a7d0945a309b
    Score: 9/25 | dice

  inKind
    IT Manager
    Austin, TX
    https://builtin.com/job/it-manager/9873125
    Score: 8/25 | builtin
```

---

## Usage

### ATS Scan Only

```bash
cd /home/fihadmin/career-sweep
python3 sweep.py scan --json
```

Returns JSON with 31 companies, filtered roles, and scores.

### Full Sweep (Local, for Testing)

```bash
cd /home/fihadmin/career-sweep
rm -f data/seen.json
python3 sweep.py scan --json  # Step 1: ATS APIs
# Step 2: agent does web_extract on 45+ boards (in cron)
python3 sweep.py merge --board-results data/board-results-YYYY-MM-DD.json --ats-results data/ats-YYYY-MM-DD.json --json
```

### Cron Schedule

```
0 6,13 * * *   (6am / 1pm PT, daily)
```

Agent-driven: runs ATS scan, scrapes all boards via web_extract in batches, merges, dedupes, scores, emails.

---

## Configuration

### `config.py`

- **SMTP:** `smtp.mail.me.com` (iCloud) — credentials in env or config
- **Target roles:** "IT Manager", "Sr IT Manager", "Senior IT Manager", "IT Operations Manager", "Infrastructure Manager"
- **Leadership + domain combos:** "Manager" / "Senior Manager" + "IT" / "Infrastructure" / "Technology"
- **Scoring:** Sr IT Manager=9, IT Manager=8, Vegas=+5, Remote=+3, Top Tech=+3
- **ATS companies:** 31 entries (Greenhouse, Ashby, Lever, Workday slugs)

### `sources/`

| Module | Purpose |
|---|---|
| `ats.py` | Greenhouse, Ashby, Lever, Workday API queries |
| `byparr.py` | Indeed, Glassdoor via Byparr (Cloudflare bypass, port 8191) |
| `camofox.py` | LinkedIn authenticated search via CamoFox (port 9377) |
| `nodriver.py` | Career pages via nodriver browser (no interaction, port 8901) |
| `direct.py` | Direct HTTP requests (Dice, RemoteOK, etc.) |
| `utils.py` | Shared: `ok_title()`, `clean()`, `score_title()` |

### Stealth Tools

| Tool | Port | Use |
|---|---|---|
| Byparr | 8191 | Cloudflare bypass (Indeed, Glassdoor, ZipRecruiter) |
| nodriver | 8901 | Browser fetch, no interaction (career pages) |
| CamoFox | 9377 | Full browser with interaction (LinkedIn auth) |

All three are optional — if unavailable, agent web_extract falls back (slower but works).

---

## Results

### E2E Test (2026-06-25)

- **ATS scan:** 1 match (Anthropic, Senior Manager, Compute Infrastructure)
- **Board scrape:** 15 raw jobs (Dice, Builtin, Talent.com, USAJobs)
- **After filter:** 4 final (2 Sr IT Manager, 2 IT Manager)
- **Scores:** HIGH=0, MEDIUM=4, LOW=0
- **Vegas:** 1 | **Remote:** 0
- **Email:** Sent ✅
- **Time:** ~2 min end-to-end

### Next Run

6am PT today.

---

## Data

### `data/` Directory

- `seen.json` — SHA256 hashes of company+title combos already scanned
- `applied.json` — Companies you've applied to (to avoid duplicates)
- `ats-YYYY-MM-DD.json` — ATS API results
- `board-results-YYYY-MM-DD.json` — Web scrape results
- `results-YYYY-MM-DD.json` — Final merged, ranked jobs
- `sweep-YYYY-MM-DD-*.txt` — Email report

All data files are `.gitignore`-d.

---

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## License

MIT. See [`LICENSE`](./LICENSE) or upstream [`CAREER_OPS_README.md`](./CAREER_OPS_README.md).

---

## Upstream Credits

This project extends [`career-ops`](https://github.com/santifer/career-ops) by santifer.

See [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md) for full credits.
