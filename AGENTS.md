# ⚠️ Hermes Career Sweep — read THIS, ignore the rest of this directory

This folder also contains the upstream **career-ops** application (`modes/`, `portals*.yml`,
`dashboard/`, `providers/`, `package.json`, dozens of `.mjs` tools, etc.).
**None of that is used for Curtis's Hermes job sweep. Do not touch it.**

## The ONLY way to run the sweep

```bash
cd /home/fihadmin/career-sweep
./run_sweep.sh            # full sweep: ATS scan + boards + merge + EMAIL
# richer results:
./run_sweep.sh prep       # scan + boards, then prints 5 URLs to scrape
#   → web_extract those 5 URLs, append rows to data/board-results-<today>.json
./run_sweep.sh send       # merge everything and SEND the email
```

When done, report one line — `email_sent: true — N roles` — and stop.

## DO NOT (every one of these has sent the agent in circles)

- ❌ Do **not** build, edit, or "configure" `portals.yml`, `profile.yml`, `modes/`, `config/`, `package.json`, a CV file, or a tracker. They already exist and are unrelated.
- ❌ Do **not** extract the resume, generate profiles, or "initialize career-sweep."
- ❌ Do **not** audit CamoFox / web_search / browser_navigate, restart proxies, or debug the stealth stack. Board scraping is just `web_extract` on the 5 URLs that `prep` prints.
- ❌ Do **not** try to log into LinkedIn or ask for LinkedIn credentials.
- ❌ Do **not** run `npm` / `npm install`. This sweep is Python; there is nothing to build.
- ❌ Do **not** summarize jobs in chat instead of running `send`. The email is the deliverable.

The authoritative instructions are the Hermes **career-sweep** skill (Quickstart at the top).
Everything else in this directory belongs to the unrelated career-ops project.
