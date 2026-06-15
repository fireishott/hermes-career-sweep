# Hermes Career Sweep

A shareable Hermes Agent job-search workflow for people who want their own agent to scan jobs, verify live postings, generate tailored resume PDFs, and email them with apply links.

This repo is a practical layer on top of the excellent MIT-licensed [`career-ops`](https://github.com/santifer/career-ops) project. The original upstream README is preserved as [`CAREER_OPS_README.md`](./CAREER_OPS_README.md), and credits are in [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md).

## What this adds

- **Hybrid scan**: ATS/API-first via `scan.mjs` (Greenhouse, Ashby, Lever) + websearch fallback for companies without scannable ATS boards.
- Title, location, and salary filtering in `portals.yml` to surface only relevant matches.
- Playwright liveness checks so dead listings do not clog the pipeline.
- Tailored resume rendering to PDF.
- Company + role names in generated resume filenames.
- Email body includes apply links so you can apply from mobile.
- Resumes stored by date/company/role:

```text
output/resumes/YYYY-MM-DD Sweep/<Company> - <Role>/<CandidateName>_<Company>_<Role>_Resume.pdf
```

## Quick start

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

## Running the scanner

The scanner supports two modes:

**ATS mode** (automatic): Companies with Greenhouse, Ashby, or Lever boards are scanned via API with zero LLM cost. `scan.mjs` auto-detects the provider and pulls all live listings.

**Websearch mode**: Companies without scannable ATS boards (custom career sites, Workday, Oracle HCM) use a `scan_query` field in `portals.yml`. Your agent runs web searches for these companies during the cron run and filters results against your title/location criteria.

Run a dry scan to see what would be found:
```bash
node scan.mjs --dry-run
```

Run a real scan (writes to `data/pipeline.md`):
```bash
node scan.mjs
```

## Email setup

`scripts/send-resume-email.py` uses your local Himalaya SMTP config at:

```text
~/.config/himalaya/config.toml
```

If you use Hermes, Gmail, iCloud, Fastmail, or another SMTP provider, wire that account into Himalaya first, then run:

```bash
python3 scripts/send-resume-email.py \
  --account your-account \
  --to you@example.com \
  --subject 'Test resume email' \
  --body 'Testing attachments' \
  --attach /path/to/resume.pdf \
  --dry-run
```

## Hermes cron prompt skeleton

Use this as the prompt for a scheduled Hermes job:

```text
Run the job sweep pipeline from this repository.

TARGET ROLES: Define your target titles, keywords, and salary range here.

STEP 1: ATS SCAN
Run `node scan.mjs` (NOT --dry-run). This scans all ATS-connected companies and writes new offers to data/pipeline.md.

STEP 2: WEBSEARCH THE REMAINING
The scan output lists companies it couldn't scan via API — marked "websearch". For EACH of those, run web_search using the scan_query from your portals.yml. Filter results against your title, location, and salary criteria.

STEP 3: REPORT
Compile ALL matches (ATS + websearch) into a single report. Group by company. Include: role title, location, URL, and level (Director/Manager/IC).

RULES:
- Do not invent jobs, URLs, salaries, or send status.
- Do not submit applications.
- Generate at most 3 resumes per run unless configured otherwise.
- Resume PDF filenames must include company and role.
- Email body must include role list, apply links, PDF filenames, and host folders.
- If no matches survive verification, do not generate filler resumes.
- Maximum 3 web_search calls per websearch company.
```

## Notes

- Generated resumes and scan data are intentionally gitignored.
- This is an agent workflow, not an application bot. It prepares materials; you still decide where to apply.
- Keep facts factual. Tailoring should emphasize relevant experience, not make up new experience.

## License

MIT. See [`LICENSE`](./LICENSE). Upstream copyright and license terms are preserved.
