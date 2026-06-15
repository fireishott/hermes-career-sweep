#!/usr/bin/env python3
import argparse
import email.message
import mimetypes
import smtplib
import subprocess
import sys
import tomllib
from pathlib import Path
from email.utils import formatdate, make_msgid

CONFIG = Path.home() / '.config' / 'himalaya' / 'config.toml'


def die(msg, code=2):
    print(f'ERROR: {msg}', file=sys.stderr)
    raise SystemExit(code)


def get_nested(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def resolve_password(auth):
    if not auth:
        die('SMTP auth block missing')
    if auth.get('password'):
        return auth['password']
    cmd = auth.get('cmd')
    if not cmd:
        die('SMTP auth.cmd missing')
    out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    if not out:
        die('SMTP auth command returned empty password')
    return out


def load_account(account):
    if not CONFIG.exists():
        die(f'missing mail config: {CONFIG}')
    data = tomllib.loads(CONFIG.read_text())
    accounts = data.get('accounts') or {}
    if account not in accounts:
        die(f'account {account!r} not found in {CONFIG}; available: {", ".join(accounts) or "none"}')
    acc = accounts[account]
    send_backend = get_nested(acc, 'message', 'send', 'backend') or {}
    auth = send_backend.get('auth') or {}
    return {
        'email': acc.get('email'),
        'display': acc.get('display-name') or acc.get('email'),
        'host': send_backend.get('host'),
        'port': int(send_backend.get('port') or 587),
        'login': send_backend.get('login') or acc.get('email'),
        'password': resolve_password(auth),
    }


def attach_file(msg, p):
    path = Path(p).expanduser().resolve()
    if not path.exists():
        die(f'attachment not found: {path}')
    ctype, enc = mimetypes.guess_type(str(path))
    maintype, subtype = (ctype or 'application/octet-stream').split('/', 1)
    data = path.read_bytes()
    msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=path.name)


def main():
    ap = argparse.ArgumentParser(description='Send email with attachments using ~/.config/himalaya SMTP config')
    ap.add_argument('--account', default=os.environ.get('JOB_SWEEP_EMAIL_ACCOUNT', 'default'))
    ap.add_argument('--to', required=True)
    ap.add_argument('--subject', required=True)
    ap.add_argument('--body', required=True)
    ap.add_argument('--attach', action='append', default=[])
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    acct = load_account(args.account)
    msg = email.message.EmailMessage()
    msg['From'] = f"{acct['display']} <{acct['email']}>"
    msg['To'] = args.to
    msg['Subject'] = args.subject
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=(acct['email'] or 'localhost').split('@')[-1])
    msg.set_content(args.body)
    for a in args.attach:
      attach_file(msg, a)

    if args.dry_run:
        print(f"DRY_RUN from={acct['email']} to={args.to} subject={args.subject!r} attachments={len(args.attach)}")
        for a in args.attach:
            p = Path(a).expanduser().resolve()
            print(f"ATTACH {p} {p.stat().st_size} bytes")
        return

    if not acct['host'] or not acct['login'] or not acct['email']:
        die('SMTP account incomplete')
    with smtplib.SMTP(acct['host'], acct['port'], timeout=45) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(acct['login'], acct['password'])
        refused = s.send_message(msg)
    if refused:
        die(f'SMTP refused recipients: {refused}', 1)
    print(f"SENT from={acct['email']} to={args.to} subject={args.subject!r} attachments={len(args.attach)}")

if __name__ == '__main__':
    main()
