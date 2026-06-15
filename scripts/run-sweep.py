#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROME_RAW = os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH', '')
BASE_RESUME = Path(os.environ.get('JOB_SWEEP_BASE_RESUME', str(ROOT / 'examples' / 'base-resume.json'))).expanduser()
CHROME = Path(CHROME_RAW).expanduser() if CHROME_RAW else None
RESUME_ROOT = Path(os.environ.get('JOB_SWEEP_RESUME_ROOT', str(ROOT / 'output' / 'resumes'))).expanduser()
DEFAULT_TO = os.environ.get('JOB_SWEEP_EMAIL_TO', '')


def run(cmd, *, cwd=ROOT, env=None, check=True):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    p = subprocess.run(cmd, cwd=cwd, env=merged, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and p.returncode != 0:
        print(p.stdout)
        raise SystemExit(p.returncode)
    return p.stdout, p.returncode


def slug(s):
    return re.sub(r'[^A-Za-z0-9]+', '-', s or '').strip('-') or 'Unknown'


def load_json(p):
    return json.loads(Path(p).read_text())


def tune_resume(base, job):
    resume = json.loads(json.dumps(base))
    company = job.get('company') or 'Target Company'
    title = job.get('title') or 'Target Role'
    contact = resume.setdefault('contact', {})
    contact['title'] = f"{title} | IT Operations, Infrastructure & AI Enablement"
    resume['target_title'] = title
    existing_summary = resume.get('summary', '').strip()
    resume['summary'] = (
        f"{title}-aligned candidate targeting {company}, with experience mapped to the role's business systems, IT operations, infrastructure, automation, and stakeholder-delivery requirements. "
        + existing_summary
    ).strip()
    # Keep the source experience factual; only front-load role alignment.
    skills = resume.get('skills') or []
    alignment = {
        'category': 'Role Alignment',
        'items': [
            title,
            company,
            'Enterprise IT Operations Leadership',
            'Infrastructure Modernization',
            'AI Enablement & Automation',
            'Vendor / MSP Governance',
        ]
    }
    resume['skills'] = [alignment] + skills
    resume.setdefault('meta', {})['accent_color'] = resume.get('meta', {}).get('accent_color') or '#0acf83'
    return resume


def parse_scan_offers(text, limit):
    offers = []
    for line in text.splitlines():
        if not line.startswith('  + '):
            continue
        # Format: + Company | Title | Location | URL
        parts = [p.strip() for p in line[4:].split('|')]
        if len(parts) < 2:
            continue
        offers.append({
            'company': parts[0],
            'title': parts[1],
            'location': parts[2] if len(parts) > 2 else '',
            'url': parts[3] if len(parts) > 3 and parts[3] else None,
        })
        if len(offers) >= limit:
            break
    return offers


def main():
    ap = argparse.ArgumentParser(description='Reliable ATS-first job sweep + resume render + email attachments')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--send-email', action='store_true')
    ap.add_argument('--to', default=DEFAULT_TO)
    ap.add_argument('--max-resumes', type=int, default=3)
    ap.add_argument('--company', action='append', default=[])
    ap.add_argument('--email-account', default=os.environ.get('JOB_SWEEP_EMAIL_ACCOUNT', 'default'))
    ap.add_argument('--skip-scan', action='store_true')
    ap.add_argument('--sample-job-json')
    args = ap.parse_args()

    env = {}
    if CHROME:
        env['PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'] = str(CHROME)
    today = datetime.now().strftime('%Y-%m-%d')
    sweep_dir = RESUME_ROOT / f'{today} Sweep'
    sweep_dir.mkdir(parents=True, exist_ok=True)

    if not BASE_RESUME.exists():
        raise SystemExit(f'Missing base resume JSON: {BASE_RESUME}')
    base = load_json(BASE_RESUME)

    scan_text = ''
    offers = []
    if args.sample_job_json:
        offers = [load_json(args.sample_job_json)]
    elif not args.skip_scan:
        cmd = ['node', 'scan.mjs', '--dry-run' if args.dry_run else '', '--verify', '--throttle=750']
        cmd = [c for c in cmd if c]
        for company in args.company:
            cmd += ['--company', company]
        scan_text, _ = run(cmd, env=env)
        offers = parse_scan_offers(scan_text, args.max_resumes)

    if not offers:
        report = {
            'status': 'no_matches',
            'sweep_dir': str(sweep_dir),
            'scan_excerpt': '\n'.join(scan_text.splitlines()[-40:]) if scan_text else '',
        }
        print(json.dumps(report, indent=2))
        return

    rendered = []
    used_dirs = set()
    for job in offers[:args.max_resumes]:
        role_dir_name = f"{slug(job.get('company'))} - {slug(job.get('title'))}"
        company_dir = sweep_dir / role_dir_name
        if company_dir in used_dirs:
            company_dir = sweep_dir / f"{role_dir_name}-{len(used_dirs) + 1}"
        used_dirs.add(company_dir)
        company_dir.mkdir(parents=True, exist_ok=True)
        job_path = company_dir / 'job.json'
        resume_path = company_dir / 'resume.json'
        job_path.write_text(json.dumps(job, indent=2))
        resume = tune_resume(base, job)
        resume_path.write_text(json.dumps(resume, indent=2))
        out, _ = run(['node', 'scripts/render-resume.mjs', '--resume', str(resume_path), '--job', str(job_path), '--out-dir', str(company_dir), '--format', 'letter'], env=env)
        manifest = load_json(company_dir / 'manifest.json')
        rendered.append({'job': job, 'folder': str(company_dir), 'pdf': manifest['pdf'], 'manifest': str(company_dir / 'manifest.json')})

    subject = f'Job sweep resumes - {today} - {len(rendered)} attachment(s)'
    body_lines = [
        f'Job sweep completed {today}.',
        '',
        'Attached resumes:',
    ]
    for item in rendered:
        j = item['job']
        body_lines.append(f"- {j.get('company')} — {j.get('title')}")
        body_lines.append(f"  Resume: {Path(item['pdf']).name}")
        body_lines.append(f"  Apply link: {j.get('url') or 'not provided by scanner'}")
        body_lines.append(f"  Host folder: {item['folder']}")
    body_lines += ['', f'Stored on host: {sweep_dir}']
    body = '\n'.join(body_lines)

    email_status = 'skipped'
    if args.send_email:
        email_cmd = ['python3', 'scripts/send-resume-email.py', '--account', args.email_account, '--to', args.to, '--subject', subject, '--body', body]
        for item in rendered:
            email_cmd += ['--attach', item['pdf']]
        if args.dry_run:
            email_cmd.append('--dry-run')
        email_out, code = run(email_cmd, check=False)
        email_status = 'sent' if code == 0 and not args.dry_run else ('dry_run' if code == 0 else 'failed')
        print(email_out)
        if code != 0:
            email_status = 'failed'

    report = {
        'status': 'ok',
        'dry_run': args.dry_run,
        'sweep_dir': str(sweep_dir),
        'rendered': rendered,
        'email_status': email_status,
        'email_to': args.to if args.send_email else None,
    }
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
