# mail-163 - 163 Mail Tool v2.3

A command-line tool for 163.com email via IMAP/SMTP, designed for [WorkBuddy](https://www.codebuddy.cn/) skills.

## Features

- List, read, search, download attachments, send emails
- Chinese keyword search support (local filtering)
- JSON output to avoid terminal encoding issues
- IMAP ID command auto-handled (avoids "Unsafe Login" error)
- Send emails with attachments and CC
- No hardcoded credentials - pass via CLI args or config file

## Quick Start

```bash
# List latest 20 emails
python3 scripts/mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE list -n 20

# Read an email
python3 scripts/mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE read 35

# Search emails (supports Chinese)
python3 scripts/mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE search "关键词"

# Download attachment
python3 scripts/mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE download 35 filename.pdf

# Send email
python3 scripts/mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE send \
  --to recipient@example.com \
  --subject "Hello" \
  --body "This is a test email"
```

## Authentication

### Option 1: CLI arguments (recommended, no credential stored on disk)

```bash
python3 scripts/mail163_tool.py --email xxx@163.com --auth-code xxxxx list
```

### Option 2: Config file

```bash
python3 scripts/mail163_tool.py config set email xxx@163.com
python3 scripts/mail163_tool.py config set auth_code xxxxx
python3 scripts/mail163_tool.py list
```

Config is stored at `~/.workbuddy/mail163.conf`.

## Notes

- Use **authorization code** (客户端授权码), not login password
- JSON output (`-o`) recommended for non-ASCII terminals
- Attachment download supports partial filename matching

## License

MIT
