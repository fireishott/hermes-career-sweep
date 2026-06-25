#!/usr/bin/env python3
"""Career Sweep v2.0 - ATS API scan + scoring. Agent handles board coverage via web_search."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import ATS_COMPANIES, DATA_DIR, SEEN_FILE, APPLIED_FILE
from sources.ats import scan_ats_companies
from pipeline import deduplicate, rank_jobs, update_seen, load_json, save_json
from mail import format_report, send_email


def run_ats_scan():
    """Run ATS API scan only - fast, reliable, returns results for agent to merge with board data."""
    start = datetime.now()
    print(f"ATS Scan starting at {start.strftime('%Y-%m-%d %H:%M:%S')}")

    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    if not Path(SEEN_FILE).exists():
        save_json(SEEN_FILE, [])
    if not Path(APPLIED_FILE).exists():
        save_json(APPLIED_FILE, [])

    # ATS APIs
    print(f"Scanning {len(ATS_COMPANIES)} ATS companies...")
    ats_jobs, ats_errors = scan_ats_companies(ATS_COMPANIES)
    print(f"Found {len(ats_jobs)} raw matches")

    # Deduplicate and rank
    unique = deduplicate(ats_jobs)
    ranked = rank_jobs(unique)

    elapsed = (datetime.now() - start).total_seconds()
    high = len([j for j in ranked if j["label"] == "HIGH"])
    medium = len([j for j in ranked if j["label"] == "MEDIUM"])
    low = len([j for j in ranked if j["label"] == "LOW"])

    print(f"\nDone in {elapsed:.1f}s")
    print(f"Total: {len(ranked)} | HIGH: {high} | MEDIUM: {medium} | LOW: {low}")

    return {
        "status": "ok",
        "elapsed_seconds": round(elapsed, 1),
        "raw_matches": len(ats_jobs),
        "filtered": len(ranked),
        "high": high, "medium": medium, "low": low,
        "jobs": ranked,
        "errors": ats_errors,
    }


def merge_and_email(board_jobs, ats_result):
    """Merge board results (from agent web_search) with ATS results, score, and email."""
    start = datetime.now()
    date_str = start.strftime("%Y-%m-%d")
    period = "morning" if start.hour < 12 else "afternoon"

    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    if not Path(SEEN_FILE).exists():
        save_json(SEEN_FILE, [])
    if not Path(APPLIED_FILE).exists():
        save_json(APPLIED_FILE, [])

    # Combine ATS + board results
    all_jobs = ats_result.get("jobs", []) + board_jobs
    source_counts = {"ats": len(ats_result.get("jobs", [])), "boards": len(board_jobs)}

    # Deduplicate and rank
    unique = deduplicate(all_jobs)
    ranked = rank_jobs(unique)

    # Update seen
    update_seen(ranked)

    # Generate report
    report = format_report(
        ranked,
        errors=ats_result.get("errors"),
        total_scanned=len(all_jobs),
        source_counts=source_counts,
    )

    # Save
    report_path = f"{DATA_DIR}/sweep-{date_str}-{period}.txt"
    Path(report_path).write_text(report)
    results_path = f"{DATA_DIR}/results-{date_str}-{period}.json"
    save_json(results_path, ranked)

    # Email
    subject = f"Career Sweep {period.title()} - {date_str} - {len(ranked)} Roles"
    email_ok = send_email(subject, report)

    high = len([j for j in ranked if j["label"] == "HIGH"])
    medium = len([j for j in ranked if j["label"] == "MEDIUM"])
    low = len([j for j in ranked if j["label"] == "LOW"])
    vegas = len([j for j in ranked if j["location_type"] == "vegas"])
    remote = len([j for j in ranked if j["location_type"] == "remote_us"])

    return {
        "status": "ok",
        "date": date_str,
        "period": period,
        "total": len(ranked),
        "high": high, "medium": medium, "low": low,
        "vegas": vegas, "remote_us": remote,
        "email_sent": email_ok,
        "report_path": report_path,
        "results_path": results_path,
        "sources": source_counts,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Career Sweep v2.0")
    sub = parser.add_subparsers(dest="command")

    # ATS scan command
    scan_p = sub.add_parser("scan", help="Run ATS API scan")
    scan_p.add_argument("--json", action="store_true")

    # Merge command
    merge_p = sub.add_parser("merge", help="Merge board results with ATS and email")
    merge_p.add_argument("--board-results", required=True, help="Path to board results JSON")
    merge_p.add_argument("--ats-results", required=True, help="Path to ATS results JSON")
    merge_p.add_argument("--dry-run", action="store_true")
    merge_p.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "scan":
        result = run_ats_scan()
        # Save ATS results
        ats_path = f"{DATA_DIR}/ats-{datetime.now().strftime('%Y-%m-%d')}.json"
        save_json(ats_path, result)
        print(f"Saved to {ats_path}")
        if args.json:
            print(json.dumps(result, indent=2))

    elif args.command == "merge":
        board_jobs = load_json(args.board_results, [])
        ats_result = load_json(args.ats_results, {})
        result = merge_and_email(board_jobs, ats_result)
        if args.json:
            print(json.dumps(result, indent=2))

    else:
        # Default: just run ATS scan
        result = run_ats_scan()
        ats_path = f"{DATA_DIR}/ats-{datetime.now().strftime('%Y-%m-%d')}.json"
        save_json(ats_path, result)
        print(json.dumps(result, indent=2))
