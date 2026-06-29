"""Email formatting and delivery."""

import os
import smtplib
import ssl
import subprocess
from datetime import datetime
from email.message import EmailMessage
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO

# Himalaya CLI is Hermes' configured email tool (sends from the same iCloud
# account as the SMTP fallback, but also files a copy in Sent). Paths are
# overridable via env so this isn't pinned to one host layout.
HIMALAYA_BIN = os.getenv(
    "HIMALAYA_BIN", "/home/fihadmin/.hermes/profiles/ignyte/home/.local/bin/himalaya"
)
HIMALAYA_CONFIG = os.getenv("HIMALAYA_CONFIG", "/home/fihadmin/.config/himalaya/config.toml")


def format_report(jobs, errors=None, ats_count=0, total_scanned=0, source_counts=None):
    """Format a clean email report from scored jobs."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%I:%M %p PT")
    is_morning = now.hour < 12
    period = "Morning" if is_morning else "Afternoon"

    high = [j for j in jobs if j["label"] == "HIGH"]
    medium = [j for j in jobs if j["label"] == "MEDIUM"]
    low = [j for j in jobs if j["label"] == "LOW"]
    vegas = [j for j in jobs if j["location_type"] == "vegas"]
    remote = [j for j in jobs if j["location_type"] == "remote_us"]

    # Source breakdown
    sc = source_counts or {}
    source_line = " | ".join(f"{k}: {v}" for k, v in sc.items() if v > 0)

    lines = [
        f"Career Sweep {period} - {date_str}",
        f"Run at {time_str}",
        "",
        f"Total: {len(jobs)} | HIGH: {len(high)} | MEDIUM: {len(medium)} | LOW: {len(low)}",
        f"Las Vegas: {len(vegas)} | Remote US: {len(remote)}",
        f"Raw jobs processed: {total_scanned}",
        f"Sources: {source_line}",
        "",
        "=" * 60,
    ]

    def add_section(label, section_jobs):
        if not section_jobs:
            return
        lines.append("")
        lines.append(label)
        lines.append("-" * 40)
        for j in section_jobs:
            loc_display = j["location"] or "Unlisted"
            lines.append(f"  {j['company']}")
            lines.append(f"    {j['title']}")
            lines.append(f"    {loc_display}")
            lines.append(f"    {j['url']}")
            lines.append(f"    Score: {j['score']}/25 | {j['source']}")
            lines.append("")

    add_section("HIGH PRIORITY (15+)", high)
    add_section("MEDIUM PRIORITY (8-14)", medium)

    if low:
        lines.append("")
        lines.append(f"LOW PRIORITY ({len(low)} roles)")
        lines.append("-" * 40)
        for j in low:
            lines.append(f"  {j['company']} | {j['title']} | {j['location']} | Score: {j['score']}")

    if errors:
        lines.append("")
        lines.append("Errors:")
        for e in errors:
            lines.append(f"  - {e}")

    lines.extend([
        "",
        "=" * 60,
        "",
        "Scoring: Sr IT Manager=9, IT Manager=8",
        "Vegas=+5, Remote=+3, Top Tech Co=+3",
        "",
        "- Career Sweep v2.0",
    ])

    return "\n".join(lines)


def send_email(subject, body):
    """Send the results email via himalaya (preferred); fall back to SMTP."""
    if _send_via_himalaya(subject, body):
        return True
    return _send_via_smtp(subject, body)


def _send_via_himalaya(subject, body):
    """Send through the himalaya CLI. Returns True on success, False to fall back."""
    if not os.path.exists(HIMALAYA_BIN):
        return False
    raw = (
        f"From: {EMAIL_FROM}\r\n"
        f"To: {EMAIL_TO}\r\n"
        f"Subject: {subject}\r\n"
        f"\r\n"
        f"{body}"
    )
    try:
        r = subprocess.run(
            [HIMALAYA_BIN, "-c", HIMALAYA_CONFIG, "message", "send"],
            input=raw, text=True, capture_output=True, timeout=60,
        )
        if r.returncode == 0:
            return True
        print(f"himalaya send failed (rc={r.returncode}): {r.stderr.strip()[:200]} — falling back to SMTP")
    except Exception as e:
        print(f"himalaya send error: {e} — falling back to SMTP")
    return False


def _send_via_smtp(subject, body):
    """iCloud SMTP fallback."""
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.ehlo()
            s.starttls(context=ssl.create_default_context())
            s.ehlo()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False
