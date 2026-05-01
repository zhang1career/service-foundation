# Mail Server Application

A complete mail server implementation with SMTP and IMAP support, storing email attachments in object storage (app_oss).

## Features

1. **SMTP Server**: Receives incoming emails and stores them
2. **IMAP Server**: Provides email access via IMAP protocol
3. **Attachment Storage**: Email attachments are stored in object storage (app_oss)
4. **Database Storage**: Email body and metadata are stored in MySQL database
5. **Multi-account Support**: Supports multiple mail accounts and mailboxes

## Architecture

```
┌─────────────┐
│ SMTP Server │  Receives emails → Parses attachments → Stores to OSS
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐     ┌───────────────┐
│ Mail Parser │────▶│     Database    │     │    app_oss    │
│   Service   │     │ (mail content + │     │ (attachments) │
└─────────────┘     │  metadata)      │     └───────────────┘
       │            └─────────────────┘
       │
       ▼
┌─────────────┐
│ IMAP Server │  Provides email access → Reads attachments from OSS
└─────────────┘
```

## Configuration

Configure in the `.env` file:

```env
# SMTP server port (default: 25)
MAIL_SMTP_PORT=25

# IMAP server port (default: 143)
MAIL_IMAP_PORT=143

# OSS bucket for mail attachments (default: mail-attachments)
MAIL_OSS_BUCKET=mail-attachments

# OSS endpoint URL (default: http://localhost:8000/api/oss)
MAIL_OSS_ENDPOINT=http://localhost:8000/api/oss

# Server host (default: 0.0.0.0)
MAIL_SERVER_HOST=0.0.0.0
```

## Database Models

### MailAccount
- Stores mail account information (username, password, domain)
- Automatically created when receiving emails for new addresses

### Mailbox
- Represents mail folders (INBOX, Sent, Drafts, etc.)
- Tracks message count and unread count

### MailMessage
- Stores email metadata and body (text and HTML)
- Links to mailbox and account
- Tracks read/deleted/flagged status

### MailAttachment
- Stores attachment metadata
- References OSS storage location (bucket and key)

## Usage

### Start Mail Servers

When `APP_MAILSERVER_ENABLED=true`, **SMTP and IMAP start automatically** with:

- `./run.sh start` or `./run_asgi.sh start`

They run as a background subprocess (`python -m app_mailserver`). The PID is stored in `/var/run/<APP_NAME>/mail_server.pid` next to `app.pid`; subprocess stdout/stderr go to `${LOG_DIR}/mail_server.log`.

Set `APP_MAILSERVER_ENABLED=false` to disable the mail app entirely (no `/api/mail/` and no SMTP/IMAP subprocess).

Manual run (debug):

```bash
python -m app_mailserver
python -m app_mailserver --smtp-only
python -m app_mailserver --imap-only
```

The management command still works and calls the same runtime:

```bash
python manage.py start_mail_server
```

### Send Email (SMTP)

Configure your email client to use:
- SMTP Server: `localhost` (or your server IP)
- SMTP Port: `25` (or configured port)
- No authentication required (for incoming mail)

### Receive Email (IMAP)

Configure your email client to use:
- IMAP Server: `localhost` (or your server IP)
- IMAP Port: `143` (or configured port)
- Login with username (email address) and password (if set)

## API Endpoints

Currently, the mail server operates via SMTP/IMAP protocols. REST API endpoints can be added in the future for management purposes.

## Storage Structure

### Database
- Email body and metadata: Stored in MySQL database
- Attachment metadata: Stored in `mail_attachment` table with OSS references

### Object Storage (OSS)
- Attachments: Stored in OSS with path format: `{account_id}/{message_id}/{filename}`
- Bucket: Configured via `MAIL_OSS_BUCKET` environment variable

## Development

### Running Tests

```bash
python manage.py test app_mailserver
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations app_mailserver

# Apply migrations
python manage.py migrate app_mailserver
```

## Notes

1. **Security**: Production deployment should implement TLS/SSL encryption and proper authentication
2. **Performance**: For high-volume scenarios, consider async processing for attachment uploads
3. **Error Handling**: OSS operations include error handling and logging
4. **IMAP Protocol**: Basic IMAP commands are implemented. Full IMAP4rev1 compliance may require additional features

## Dependencies

- `aiosmtpd`: Async SMTP server library
- `boto3`: S3 client for OSS integration
- Django ORM: Database operations
- Python `email` module: Email parsing

