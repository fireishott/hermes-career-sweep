# Hermes Career Sweep

A shareable Hermes Agent job-search workflow — parallel subagent pipeline that scans priority job boards, verifies live postings, ranks by fit, and emails results with direct apply links.

Built on [`career-ops`](https://github.com/santifer/career-ops) by santifer. Upstream README preserved as [`CAREER_OPS_README.md`](./CAREER_OPS_README.md). Credits in [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md).

## What this adds

- **Subagent architecture** — one orchestrator spawns 4 parallel subagents, each scanning a different board category. Eliminates single-agent timeout on long sweeps.
- **Stealth browser integration** — CamoFox (anti-bot) and Byparr (Cloudflare bypass) for scraping protected job boards that block standard requests.
- **ATS/API-first scan** — `scan.mjs` hits Greenhouse, Ashby, and Lever APIs directly (zero LLM cost).
- **100+ job boards** — comprehensive coverage across aggregators, remote specialists, tech, executive, and local sources.
- **Clean email output** — results arrive as a formatted table with direct apply links, grouped by fit tier, no walls of text.
- **Liveness verification** — Playwright checks confirm each listing is still live before including in results.
- **Tailored resume rendering** — generates per-role PDFs from a base resume + job description.
- **Deduplication** — cross-references against applied companies and self-duplicates across boards.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   ORCHESTRATOR                      │
│              (1 agent, top-level)                   │
│                                                     │
│  1. Get today's date                                │
│  2. Spawn 4 subagents in parallel                   │
│  3. Compile results                                 │
│  4. Deduplicate                                     │
│  5. Rank by fit                                     │
│  6. Email clean results                             │
│  7. Update tracker                                  │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────────┐
        ▼          ▼          ▼              ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
   │ SUB A   │ │ SUB B   │ │ SUB C   │ │ SUB D    │
   │ ATS     │ │ Stealth │ │ Remote/ │ │ Local    │
   │ Scan    │ │ Boards  │ │ Tech    │ │ Boards   │
   └─────────┘ └─────────┘ └─────────┘ └──────────┘
```

### Subagent A: ATS Scan
- Runs `node scan.mjs` from the career-ops repo
- Scans Greenhouse, Ashby, and Lever ATS boards via API
- Returns matching roles as JSON

### Subagent B: Stealth Browser Boards
- **Indeed** — Byparr (Cloudflare bypass): `POST http://127.0.0.1:8191/v1`
- **LinkedIn** — CamoFox (authenticated login with your credentials)
- **Glassdoor** — Byparr (Cloudflare bypass)
- **Google Jobs** — CamoFox for `jobs.google.com` searches
- Returns matching roles with direct apply links where possible

### Subagent C: Tech & Remote Boards
- **web_search** each board individually:
  - Dice, Built In, We Work Remotely, Remote100K, FlexJobs, Wellfound, The Ladders, 6FigureJobs
  - General queries: "IT Manager remote", "Senior IT Manager remote", "IT Infrastructure Manager"
- Returns matching roles as JSON

### Subagent D: Local & Regional Boards
- **web_search** each employer/board:
  - Local companies, state job portals, regional employers
  - Employer career pages with known ATS systems
- Returns matching roles as JSON

Each subagent gets its own isolated context and terminal session. Results are merged, deduplicated, and ranked by the orchestrator.

---

## Job Board Master List

100+ boards across 10 categories. The pipeline scans all of them — no cherry-picking.

### Mega Aggregators (must-scan every run)

| Board | Access Method | Notes |
|-------|---------------|-------|
| Indeed | Byparr (`POST http://127.0.0.1:8191/v1`) | Cloudflare protected. Byparr required. |
| LinkedIn Jobs | CamoFox (authenticated) | Login flow required. CAPTCHA may trigger on VPN. |
| Glassdoor | Byparr | Cloudflare protected. Byparr required. |
| Google Jobs | CamoFox or web_search | `jobs.google.com` — best single source when it renders. |
| ZipRecruiter | Byparr or web_search | |
| Monster | web_search | |
| CareerBuilder | web_search | |
| SimplyHired | web_search | |

### Remote Specialists

| Board | URL | Notes |
|-------|-----|-------|
| We Work Remotely | weworkremotely.com | Curated remote listings |
| RemoteOK | remoteok.com | |
| Remote.co | remote.co | |
| FlexJobs | flexjobs.com | Paid model, use web_search |
| Remotive | remotive.com | Tech remote jobs |
| Working Nomads | workingnomads.com | |
| Jobspresso | jobspresso.co | Remote tech jobs |

### High-Paying / Executive

| Board | URL | Notes |
|-------|-----|-------|
| The Ladders | theladders.com | $100K+ focus |
| 6FigureJobs | 6figurejobs.com | |
| Hired | hired.com | Vetted candidates |
| Lenny's Jobs | lennysjobs.com | Product/tech |
| Built In | builtin.com | Tech companies, salary data |

### Tech-Specific

| Board | URL | Notes |
|-------|-----|-------|
| Dice | dice.com | IT & tech primary |
| Built In | builtin.com | Local + remote tech |
| GitHub Jobs | jobs.github.com | Engineering |
| Stack Overflow Jobs | stackoverflow.com/jobs | |
| Hacker News (Who's Hiring) | news.ycombinator.com | Monthly threads |
| AngelList / Wellfound | wellfound.com | Startup jobs, equity data |
| Otta | otta.com | Tech-focused |
| Braintrust | talent.chainbraintrust.com | Web3/remote |
| Turing | turing.com | Remote dev roles |

### Executive / Professional

| Board | URL | Notes |
|-------|-----|-------|
| Ladders | theladders.com | $100K+ |
| ExecuNet | execunet.com | Executive network |
| Robert Half | roberthalf.com | |
| Kforce | kforce.com | IT staffing |
| TEKsystems | teksystems.com | IT staffing |

### Federal / Government

| Board | URL | Notes |
|-------|-----|-------|
| USAJobs | usajobs.gov | Federal positions |
| GovernmentJobs | governmentjobs.com | State and local |
| ClearanceJobs | clearancejobs.com | Security clearance |
| IntelligenceCareers | iccareers.gov | |

### Staffing / Agencies

| Board | URL | Notes |
|-------|-----|-------|
| Robert Half | roberthalf.com | |
| Kforce | kforce.com | |
| TEKsystems | teksystems.com | |
| Insight Global | insightglobal.com | |
| Aerotek | aerotek.com | |
| Randstad | randstad.com | |
| Adecco | adecco.com | |

### Aggregator / Meta-Search Tools

| Tool | URL | Notes |
|------|-----|-------|
| Jobscan | jobscan.co | Resume vs JD matching |
| Huntr | huntr.co | Job tracking + search |
| Teal | tealhq.com | Job search tracker |
| LoopCV | loopcv.me | Auto-apply tool |
| LazyApply | lazyapply.com | Auto-apply |
| Sonara | sonara.ai | AI job matching |

### Research / Signal

| Source | URL | Notes |
|--------|-----|-------|
| Levels.fyi | levels.fyi | Comp data |
| Glassdoor | glassdoor.com | Reviews + salary |
| Blind | teamblind.com | Anonymous insider info |
| Fishbowl | joinfishbowl.com | Professional discussions |
| Built In | builtin.com | Company + salary data |

---

## Results Email Format

Clean, scannable, no walls of text. Direct apply links to specific postings.

```
Job Sweep Morning — 2026-06-23 — 12 Prospects

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IT MANAGER / SR MANAGER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Company              | Title                    | Location     | Apply Link                           | Source
Acme Corp            | IT Operations Manager    | Remote       | https://boards.greenhouse.io/acme/123  | Dice
TechCo               | Sr IT Manager            | Remote US    | https://lever.co/techco/456           | LinkedIn
FinanceGroup         | IT Infrastructure Mgr    | Hybrid       | https://workday.com/fingroup/789       | Indeed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIRECTOR+ (Remote/Vegas Only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Company              | Title                    | Location     | Apply Link                           | Source
BigCo                | Director of IT Ops       | Remote       | https://greenhouse.io/bigco/101       | Built In

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total: 12 prospects
Remote: 8 | Local: 4 | $130K+: 6
Already applied: 3 removed | Duplicates: 5 removed
```

### Email rules
- **Direct apply links only.** Never `company.com/careers` — find the specific posting URL (ATS board URL preferred).
- **Apply link must point to the specific posting**, not the company's careers homepage.
- Group by score tier (IT Manager/Sr Manager first, Director+ second).
- Footer with totals: remote count, local count, salary bracket breakdown.
- Sent via Python `smtplib` (no external dependencies).

---

## Quick Start

```bash
npm install
cp portals.example.yml portals.yml
cp .env.example .env
```

Edit:
- `examples/base-resume.json` — replace with your factual resume data.
- `portals.yml` — set companies, keywords, location and salary filters.
- `.env` — set `JOB_SWEEP_EMAIL_TO`, resume output path, and optional Chrome path.

Run a dry test with a sample job:
```bash
python3 scripts/run-sweep.py --dry-run --send-email --sample-job-json examples/sample-job.json --max-resumes 1
```

### Running the scanner

**ATS mode** (automatic): Companies with Greenhouse, Ashby, or Lever boards are scanned via API with zero LLM cost. `scan.mjs` auto-detects the provider and pulls all live listings.

**Websearch mode**: Companies without scannable ATS boards use a `scan_query` field in `portals.yml`. The agent runs web searches for these companies during the cron run.

```bash
node scan.mjs --dry-run    # preview
node scan.mjs              # real scan → writes to data/pipeline.md
```

### Email setup

```bash
python3 scripts/send-resume-email.py \
  --account your-account \
  --to you@example.com \
  --subject 'Test resume email' \
  --body 'Testing attachments' \
  --attach /path/to/resume.pdf \
  --dry-run
```

---

## Hermes Cron Prompt Skeleton

```text
Curtis Freeman job sweep — parallel subagent architecture. You are the ORCHESTRATOR.

TARGETS:
PRIMARY: IT Manager, Sr IT Manager, IT Operations Manager, IT Infrastructure Manager,
Service Delivery Manager, Desktop Engineering Manager, Endpoint Manager, IT Program Manager,
Workplace Technology Manager, IT Service Manager.

SECONDARY: IT Director, Director of IT Operations — ONLY include if 100% remote and a
clear operations/infrastructure fit.

LOCATION: Remote (anywhere US) or local ONLY. No relocation-required roles.
SALARY: $130K+ preferred. Include $100K-$129K if strong fit. Skip below $100K.

SPAWN 4 SUBAGENTS IN PARALLEL using delegate_task (tasks array):

SUBAGENT A (workdir /home/fihadmin/job-sweep):
Run `node scan.mjs`, then read data/pipeline.md. Filter to matching roles.
Return JSON: [{"company", "title", "location", "url", "source":"ATS", "location_type"}]

SUBAGENT B (Stealth browser boards):
Indeed via Byparr. LinkedIn via CamoFox (auth: your@email.com / your-password).
Glassdoor via Byparr. Google Jobs via CamoFox.
Return JSON with direct apply links.

SUBAGENT C (Tech/remote boards):
web_search: Dice, Built In, We Work Remotely, Remote100K, FlexJobs, Wellfound, Ladders.
Return JSON list.

SUBAGENT D (Local/regional boards):
web_search: Local employers, state portals, regional companies.
Return JSON list.

AFTER SUBAGENTS:
1. Merge all results
2. Deduplicate (same company + similar title → keep best URL)
3. Rank: Remote > Local. IT Manager/Sr Manager > Director.
4. Clean email: table with Company | Title | Location | Apply URL | Source
5. Group: IT Manager section first, Director section second
6. Email from your address via smtplib
7. Update tracker
```

---

## Stealth Browser Setup

The pipeline uses two self-hosted services for scraping protected job boards:

### CamoFox (primary stealth browser)
- **URL:** `http://127.0.0.1:9377`
- **Auth:** Set via `CAMOFOX_API_KEY` environment variable (see `.env.example`)
- **Use for:** All board scraping, login flows, SPA interaction
- **How it works:** C++ engine-level anti-bot bypass. Not JS injection — actual browser fingerprinting evasion.
- **Best for:** LinkedIn (authenticated), Google Jobs, any site with bot detection

### Byparr (Cloudflare/CAPTCHA bypass)
- **URL:** `http://127.0.0.1:8191/v1`
- **Auth:** None (FlareSolverr-compatible API)
- **Use for:** Indeed, Glassdoor — sites behind Cloudflare that block standard requests
- **How it works:** Solves Cloudflare challenges and passes cookies for subsequent requests

### Failover order
1. Try CamoFox first
2. If blocked/CAPTCHA'd → try Byparr
3. If both fail → flag as UNVERIFIED, include with warning

---

## Notes

- Generated resumes and scan data are gitignored.
- This is an agent workflow, not an application bot. It prepares materials; you still decide where to apply.
- Keep facts factual. Tailoring should emphasize relevant experience, not fabricate new experience.
- Subagents have no memory of the orchestrator's conversation. All instructions must be self-contained in the `delegate_task` prompt.

## License

MIT. See [`LICENSE`](./LICENSE). Upstream copyright and license terms are preserved.