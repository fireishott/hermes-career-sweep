# Acknowledgments

This project stands on top of real work from the open-source AI job-search ecosystem.

## Upstream foundation

- **career-ops** by Santiago Fernández de Valderrama — MIT licensed.  
  Original project: https://github.com/santifer/career-ops  
  The portal scanner, career workflow concepts, provider architecture, templates, and agent-facing operating model come from that project.

## Runtime dependencies

- **Playwright** — browser automation and PDF rendering.
- **js-yaml** — YAML config parsing.
- **Hermes Agent** — intended orchestration runtime for scheduled autonomous sweeps.

## This fork/layer

This repository adds a Hermes-oriented daily sweep layer:

- ATS/API-first job scanning with liveness verification.
- Resume PDF rendering with company/role-specific filenames.
- Email delivery with resume attachments and mobile-ready apply links.
- Host-folder organization by sweep date, company, and role.
- Example cron prompt/workflow for running it from a personal Hermes agent.

Keep the upstream MIT license intact when redistributing or modifying this project.
