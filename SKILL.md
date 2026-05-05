---
name: mail-163
description: "163邮箱邮件工具，支持收件箱列表、读取邮件、搜索邮件、发送邮件、下载附件。通过参数指定邮箱和授权码，结果输出到JSON文件避免乱码。当用户需要收取163邮件、查看邮件列表、搜索邮件、发送邮件、下载附件时使用此Skill。"
metadata:
  {
    "clawdbot":
      {
        "emoji": "📧",
        "requires": { "bins": ["python3"] },
        "tags": ["163邮箱", "邮件", "imap", "smtp", "收件箱", "附件", "发送邮件", "email"]
      },
  }
---

# 163 邮箱邮件工具 v2.3

通过 163 邮箱的 IMAP/SMTP 协议，在命令行中收邮件、读正文、搜索邮件、发送邮件、下载附件。

## 重要特性

- ✅ 支持中文搜索（IMAP搜索只支持ASCII，本工具在本地过滤支持中文）
- ✅ 结果输出到JSON文件，避免终端乱码
- ✅ 参数化登录，无需配置文件即可使用
- ✅ IMAP ID命令自动发送，避免"Unsafe Login"错误
- ✅ 支持发送邮件（含附件、CC）

## 认证方式

### 方式1：命令行参数（推荐）

```bash
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx <command>
```

### 方式2：配置文件

```bash
python3 mail163_tool.py config set email xxx@163.com
python3 mail163_tool.py config set auth_code xxxxx
```

## 命令用法

### 1. 列出邮件列表

```bash
# 列出最新10封邮件到JSON文件
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx list -n 10 -o /tmp/mails.json

# 直接显示（可能有乱码）
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx list
```

### 2. 读取邮件内容

```bash
# 读取邮件并保存到JSON
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx read 35 -o /tmp/mail35.json
```

### 3. 搜索邮件（支持中文）

```bash
# 搜索包含"龙族"的邮件
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx search 龙族 -o /tmp/shimen.json

# 搜索发件人
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx search idea2real -o /tmp/search.json
```

### 4. 下载附件

```bash
# 下载邮件35的附件（支持部分匹配）
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx download 35 hk-ipo

# 下载到指定目录
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx download 35 hk-ipo -o ~/Desktop
```

### 5. 发送邮件

```bash
# 发送简单邮件
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx send \
  --to recipient@163.com \
  --subject "邮件主题" \
  --body "邮件正文内容"

# 发送带附件的邮件
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx send \
  --to recipient@163.com \
  --subject "带附件的邮件" \
  --body "请查看附件" \
  --attachment /path/to/file.zip

# 发送带多个附件的邮件
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx send \
  --to recipient@163.com \
  --subject "多附件邮件" \
  --body "请查看附件" \
  --attachment file1.pdf file2.xlsx

# 发送带CC的邮件
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx send \
  --to recipient@163.com \
  --cc "cc1@163.com,cc2@gmail.com" \
  --subject "带抄送的邮件" \
  --body "正文内容"

# 正文从文件读取（以@开头）
python3 mail163_tool.py --email xxx@163.com --auth-code xxxxx send \
  --to recipient@163.com \
  --subject "长邮件" \
  --body "@/tmp/long_body.txt"
```

## 快速使用示例

```bash
# 查看收件箱
python3 mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE list -n 20 -o /tmp/inbox.json

# 读取邮件
python3 mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE read 32 -o /tmp/mail32.json

# 搜索邮件
python3 mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE search 关键词 -o /tmp/search.json

# 下载附件
python3 mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE download 35 filename

# 发送邮件
python3 mail163_tool.py --email YOUR_EMAIL@163.com --auth-code YOUR_AUTH_CODE send \
  --to recipient@example.com \
  --subject "邮件主题" \
  --body "邮件正文内容"
```

## 输出JSON格式

### list 命令输出

```json
{
  "total": 36,
  "count": 5,
  "emails": [
    {
      "id": "36",
      "date": "2026-05-02 13:55",
      "from": "sender@163.com",
      "subject": "邮件主题"
    }
  ]
}
```

### read 命令输出

```json
{
  "id": "32",
  "from": "sender@example.com",
  "to": "YOUR_EMAIL@163.com",
  "date": "2026-05-01 17:49",
  "subject": "邮件主题",
  "body": "师父、各位师兄弟：\n\n大家好...",
  "attachments": []
}
```

## 注意事项

1. **授权码**：163邮箱使用"客户端授权码"，不是登录密码
2. **安全**：建议通过参数传递凭据，用完不留痕
3. **中文搜索**：IMAP协议本身不支持中文搜索，本工具通过获取全部邮件后在本地过滤实现
4. **附件下载**：支持附件名部分匹配，如 `hk-ipo` 可匹配 `hk-ipo-reminder.tar.gz`

## 故障排除

### "Unsafe Login" 错误

确保使用了IMAP ID命令。本工具已自动处理。

### 中文乱码

使用 `-o` 参数输出到JSON文件，然后用Python读取：
```bash
python3 -c "import json; print(json.load(open('/tmp/mails.json'), ensure_ascii=False))"
```

## 文件路径

- 脚本：`~/.workbuddy/skills/mail-163/scripts/mail163_tool.py`
- 配置文件：`~/.workbuddy/mail163.conf`
