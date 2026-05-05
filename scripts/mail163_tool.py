#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
163 邮箱邮件工具 v2.3 - 稳定版
支持参数化登录、筛选邮件、发送邮件、下载附件、JSON输出

用法:
  python mail163_tool.py --email xxx@163.com --auth-code xxxxx list -n 20 -o /tmp/mails.json
  python mail163_tool.py --email xxx@163.com --auth-code xxxxx read 35 -o /tmp/mail35.json
  python mail163_tool.py --email xxx@163.com --auth-code xxxxx search dragon -o /tmp/search.json
  python mail163_tool.py --email xxx@163.com --auth-code xxxxx download 35 file.tar.gz
  python mail163_tool.py --email xxx@163.com --auth-code xxxxx send --to xxx@163.com --subject "主题" --body "正文"
  python mail163_tool.py --email xxx@163.com --auth-code xxxxx send --to xxx@163.com --subject "主题" --body "@/tmp/body.txt"
"""
from __future__ import print_function

import os
import sys
import json
import imaplib
import smtplib
import email
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import decode_header
from pathlib import Path

# Force UTF-8 encoding for stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CONF_PATH = Path.home() / ".workbuddy" / "mail163.conf"
IMAP_SERVER = "imap.163.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.163.com"
SMTP_PORT = 465
IMAP_ID = ("name", "WorkBuddy-mail163", "version", "2.3", "vendor", "WorkBuddy", "support-email", "YOUR_EMAIL@example.com")


def load_conf():
    if CONF_PATH.exists():
        with open(CONF_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def decode_str(s):
    if s is None:
        return ""
    parts = decode_header(s)
    result = []
    for data, charset in parts:
        if isinstance(data, bytes):
            result.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(data)
    return "".join(result)


def format_date(date_str):
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return date_str


def get_credentials(args):
    addr = args.email or os.environ.get("MAIL163_EMAIL")
    auth_code = args.auth_code or os.environ.get("MAIL163_AUTH_CODE")
    conf = load_conf()
    addr = addr or conf.get("email")
    auth_code = auth_code or conf.get("auth_code")
    if not addr or not auth_code:
        sys.exit("Error: missing email or auth-code")
    return addr, auth_code


def prepare_imap(conn):
    if "ID" not in imaplib.Commands:
        imaplib.Commands["ID"] = ("AUTH",)
    try:
        payload = '("' + '" "'.join(IMAP_ID) + '")'
        conn._simple_command("ID", payload)
    except Exception:
        pass


def connect_imap(addr, auth_code):
    conn = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    conn.login(addr, auth_code)
    prepare_imap(conn)
    conn.select("INBOX")
    return conn


def connect_smtp(addr, auth_code):
    """连接163 SMTP服务器（SSL）"""
    conn = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    conn.login(addr, auth_code)
    return conn


def extract_body(msg):
    body, attachments = "", []
    for part in msg.walk():
        ct = part.get_content_type()
        disp = str(part.get("Content-Disposition", ""))
        if "attachment" in disp:
            fn = decode_str(part.get_filename() or "")
            if fn:
                attachments.append(fn)
        elif ct == "text/plain":
            try:
                cs = part.get_content_charset() or "utf-8"
                body = part.get_payload(decode=True).decode(cs, errors="replace")
            except Exception:
                pass
        elif ct == "text/html" and not body:
            try:
                cs = part.get_content_charset() or "utf-8"
                body = part.get_payload(decode=True).decode(cs, errors="replace")
            except Exception:
                pass
    return body, attachments


def _p(msg):
    """Safe print with UTF-8"""
    sys.stdout.write(str(msg) + "\n")
    sys.stdout.flush()


def cmd_list(args):
    addr, auth_code = get_credentials(args)
    count = args.count or 10
    output = args.output

    try:
        conn = connect_imap(addr, auth_code)
        _, msgs = conn.search(None, "ALL")
        ids = msgs[0].split()
        total = len(ids)
        recent = ids[-count:] if total > count else ids

        emails = []
        for eid in reversed(recent):
            _, data = conn.fetch(eid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if data and data[0]:
                msg = email.message_from_bytes(data[0][1])
                emails.append({
                    "id": eid.decode(),
                    "date": format_date(msg.get("Date", "")),
                    "from": decode_str(msg.get("From", "")),
                    "subject": decode_str(msg.get("Subject", "")),
                })
        conn.logout()

        result = {"total": total, "count": len(emails), "emails": emails}

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            _p(f"[OK] Saved {len(emails)} emails to {output}")
        else:
            _p(f"\n=== Inbox ({total} emails, showing {len(emails)}) ===")
            for e in emails:
                _p(f"[{e['id']:>4}] {e['date']}  {e['from'][:30]:<30}")
                _p(f"       {e['subject'][:50]}\n")

        return result
    except Exception as ex:
        _p(f"[ERROR] {ex}")


def cmd_read(args):
    addr, auth_code = get_credentials(args)
    mail_id = args.mail_id
    output = args.output

    try:
        conn = connect_imap(addr, auth_code)
        _, data = conn.fetch(mail_id, "(RFC822)")
        conn.logout()

        if not data or not data[0]:
            _p(f"[ERROR] Mail #{mail_id} not found")
            return

        msg = email.message_from_bytes(data[0][1])
        body, attachments = extract_body(msg)

        result = {
            "id": mail_id,
            "from": decode_str(msg.get("From", "")),
            "to": decode_str(msg.get("To", "")),
            "date": format_date(msg.get("Date", "")),
            "subject": decode_str(msg.get("Subject", "")),
            "body": body,
            "attachments": attachments
        }

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            _p(f"[OK] Saved mail #{mail_id} to {output}")
        else:
            _p("=" * 70)
            _p(f"From: {result['from']}")
            _p(f"Date: {result['date']}")
            _p(f"Subject: {result['subject']}")
            _p("-" * 70)
            _p(result['body'][:2000] if result['body'] else "(No body)")
            if attachments:
                _p(f"\nAttachments: {attachments}")
            _p("=" * 70)

        return result
    except Exception as ex:
        _p(f"[ERROR] {ex}")


def cmd_search(args):
    addr, auth_code = get_credentials(args)
    keyword = args.keyword
    count = args.count or 20
    output = args.output

    try:
        conn = connect_imap(addr, auth_code)
        _, msgs = conn.search(None, "ALL")
        ids = msgs[0].split()

        # 过滤匹配的邮件（在本地用Python处理，支持中文）
        emails = []
        for eid in ids:
            _, data = conn.fetch(eid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if data and data[0]:
                msg = email.message_from_bytes(data[0][1])
                subject = decode_str(msg.get("Subject", ""))
                sender = decode_str(msg.get("From", ""))
                # 检查关键词是否匹配（不区分大小写）
                if keyword.lower() in subject.lower() or keyword.lower() in sender.lower():
                    emails.append({
                        "id": eid.decode(),
                        "date": format_date(msg.get("Date", "")),
                        "from": sender,
                        "subject": subject,
                    })

        conn.logout()

        if not emails:
            _p(f"[INFO] No emails found matching '{keyword}'")
            return []

        # 最新的在前面，取前count条
        emails = list(reversed(emails))[:count]
        total = len(emails)  # 这是过滤后的总数

        result = {"keyword": keyword, "total": total, "count": len(emails), "emails": emails}

        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            _p(f"[OK] Found {total} emails, saved {len(emails)} to {output}")
        else:
            _p(f"\n=== Search '{keyword}' ({total} found, showing {len(emails)}) ===")
            for e in emails:
                _p(f"[{e['id']:>4}] {e['date']}  {e['from'][:30]:<30}")
                _p(f"       {e['subject'][:50]}\n")

        return emails
    except Exception as ex:
        _p(f"[ERROR] {ex}")


def cmd_download(args):
    addr, auth_code = get_credentials(args)
    mail_id = args.mail_id
    attachment = args.attachment
    out_dir = Path(args.output_dir) if args.output_dir else Path.home() / "Downloads"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        conn = connect_imap(addr, auth_code)
        _, data = conn.fetch(mail_id, "(RFC822)")
        conn.logout()

        if not data or not data[0]:
            _p(f"[ERROR] Mail #{mail_id} not found")
            return

        msg = email.message_from_bytes(data[0][1])

        for part in msg.walk():
            disp = str(part.get("Content-Disposition", ""))
            if "attachment" in disp:
                fn = decode_str(part.get_filename() or "")
                if fn and (fn == attachment or attachment in fn):
                    content = part.get_payload(decode=True)
                    if content:
                        filepath = out_dir / fn
                        with open(filepath, "wb") as f:
                            f.write(content)
                        size = len(content)
                        _p(f"[OK] Downloaded: {filepath} ({size/1024:.1f} KB)")
                        return

        _p(f"[ERROR] Attachment '{attachment}' not found in mail #{mail_id}")
        _, attachments = extract_body(msg)
        if attachments:
            _p(f"Available: {attachments}")
    except Exception as ex:
        _p(f"[ERROR] {ex}")


def cmd_send(args):
    """发送邮件"""
    addr, auth_code = get_credentials(args)
    to_addr = args.to
    subject = args.subject
    body = args.body
    cc_addr = args.cc
    attachment = args.attachment

    if not to_addr or not subject or not body:
        _p("[ERROR] Missing required: --to, --subject, --body")
        return

    # 如果body是文件路径，读取文件内容
    if body.startswith("@"):
        body_file = body[1:]
        try:
            with open(body_file, 'r', encoding='utf-8') as f:
                body = f.read()
        except Exception as ex:
            _p(f"[ERROR] Cannot read body file: {ex}")
            return

    try:
        # 构建邮件
        msg = MIMEMultipart()
        msg['From'] = addr
        msg['To'] = to_addr
        if cc_addr:
            msg['Cc'] = cc_addr
        msg['Subject'] = subject

        # 添加正文
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 添加附件
        if attachment:
            att_files = attachment if isinstance(attachment, list) else [attachment]
            for att_file in att_files:
                att_path = Path(att_file)
                if not att_path.exists():
                    _p(f"[WARN] Attachment not found: {att_file}, skipping")
                    continue
                with open(att_path, 'rb') as f:
                    att_data = f.read()
                att_name = att_path.name
                part = MIMEApplication(att_data, Name=att_name)
                part['Content-Disposition'] = f'attachment; filename="{att_name}"'
                msg.attach(part)

        # 连接SMTP并发送
        smtp_conn = connect_smtp(addr, auth_code)

        # 收集收件人列表
        recipients = [to_addr]
        if cc_addr:
            recipients.extend([x.strip() for x in cc_addr.split(',')])

        smtp_conn.send_message(msg, addr, recipients)
        smtp_conn.quit()

        _p(f"[OK] Email sent successfully!")
        _p(f"  From: {addr}")
        _p(f"  To: {to_addr}")
        if cc_addr:
            _p(f"  Cc: {cc_addr}")
        _p(f"  Subject: {subject}")

    except Exception as ex:
        _p(f"[ERROR] Failed to send email: {ex}")


def main():
    parser = argparse.ArgumentParser(description="163 Mail Tool v2.3")
    parser.add_argument("--email", help="163 email address")
    parser.add_argument("--auth-code", help="163 authorization code")

    sub = parser.add_subparsers(dest="cmd", help="Commands: list, read, search, download, send")

    p_list = sub.add_parser("list", help="List emails")
    p_list.add_argument("-n", "--count", type=int, default=10)
    p_list.add_argument("-o", "--output", help="Output JSON file")

    p_read = sub.add_parser("read", help="Read email")
    p_read.add_argument("mail_id", help="Email ID")
    p_read.add_argument("-o", "--output", help="Output JSON file")

    p_search = sub.add_parser("search", help="Search emails")
    p_search.add_argument("keyword", help="Search keyword")
    p_search.add_argument("-n", "--count", type=int, default=20)
    p_search.add_argument("-o", "--output", help="Output JSON file")

    p_dl = sub.add_parser("download", help="Download attachment")
    p_dl.add_argument("mail_id", help="Email ID")
    p_dl.add_argument("attachment", help="Attachment filename")
    p_dl.add_argument("-o", "--output-dir", help="Output directory")

    p_send = sub.add_parser("send", help="Send email")
    p_send.add_argument("--to", required=True, help="Recipient email address")
    p_send.add_argument("--subject", required=True, help="Email subject")
    p_send.add_argument("--body", required=True, help="Email body (use @/path/to/file.txt for file content)")
    p_send.add_argument("--cc", help="CC recipient(s), comma separated")
    p_send.add_argument("--attachment", nargs="*", help="Attachment file(s)")

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        sys.exit(0)

    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "read":
        cmd_read(args)
    elif args.cmd == "search":
        cmd_search(args)
    elif args.cmd == "download":
        cmd_download(args)
    elif args.cmd == "send":
        cmd_send(args)


if __name__ == "__main__":
    main()