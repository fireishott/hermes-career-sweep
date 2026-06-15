# Hermes Career Sweep

A shareable Hermes Agent job-search workflow for people who want their own agent to scan jobs, verify live postings, generate tailored resume PDFs, and email them with apply links.

This repo is a practical layer on top of the excellent MIT-licensed [`career-ops`](https://github.com/santifer/career-ops) project. The original upstream README is preserved as [`CAREER_OPS_README.md`](./CAREER_OPS_README.md), and credits are in [`ACKNOWLEDGMENTS.md`](./ACKNOWLEDGMENTS.md).

## What this adds

- ATS/API-first scanning via `scan.mjs`.
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

Run a real scan:

```bash
node validate-portals.mjs portals.yml
python3 scripts/run-sweep.py --send-email --max-resumes 3
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
Run the job sweep from this repository.

Rules:
- Do not invent jobs, URLs, salaries, or send status.
- Do not submit applications.
- Generate at most 3 resumes per run unless I ask otherwise.
- Resume PDF filenames must include company and role.
- Email body must include role list, apply links, PDF filenames, and host folders.
- If no matches survive verification, do not generate filler resumes.

Steps:
1. Run node validate-portals.mjs portals.yml.
2. Run python3 scripts/run-sweep.py --send-email --max-resumes 3.
3. Final response: roles found, apply links, PDFs generated, exact host folder(s), email result, blockers.
```

## Notes

- Generated resumes and scan data are intentionally gitignored.
- This is an agent workflow, not an application bot. It prepares materials; you still decide where to apply.
- Keep facts factual. Tailoring should emphasize relevant experience, not make up new experience.

## License

MIT. See [`LICENSE`](./LICENSE). Upstream copyright and license terms are preserved.
