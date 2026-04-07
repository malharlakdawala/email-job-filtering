# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

A Python CLI tool that filters job application emails in Gmail using Claude AI. It classifies emails into 4 categories (POSITIVE, NEGATIVE, NEUTRAL, SKIP) and either labels positive emails for review or trashes the rest.

## Running the Script

```bash
# Install dependencies
pip install -r requirements.txt

# Dry run (preview classifications, no changes)
python filter_emails.py --dry-run --max-emails 10

# Actual run
python filter_emails.py

# Override defaults
python filter_emails.py --days 14 --max-emails 50 --label "Jobs/Interesting"
```

## Architecture

Four Python files, no packages or subdirectories:

- **`filter_emails.py`** — Entry point. Argparse CLI, orchestration loop (fetch → classify → act), prints summary. Calls into `gmail_client` and `classifier`.
- **`gmail_client.py`** — Gmail API wrapper. Handles OAuth2 auth (`token.json`/`credentials.json`), email fetching with pagination, body decoding (multipart-aware), label creation, batch trash/label operations.
- **`classifier.py`** — Sends batches of emails to Claude (`claude-haiku-4-5`) with a system prompt defining 4 categories. Parses JSON response.
- **`config.py`** — All default constants (Gmail query, label name, batch sizes, model). CLI args in `filter_emails.py` override these.

**Data flow:** Gmail search query → paginated message IDs → batch fetch details (from, subject, body snippet) → batch classify via Claude → batch trash or label.

**Idempotency:** The Gmail query excludes already-labeled and trashed emails, so re-running is safe.

## Prerequisites

1. `credentials.json` from Google Cloud Console (OAuth 2.0 Desktop app, Gmail API enabled)
2. `ANTHROPIC_API_KEY` env var (from Claude Max Plan at console.anthropic.com)

## Key Design Decisions

- Uses `gmail.modify` scope (minimum needed for read + label + trash)
- Uses `claude-haiku-4-5` for classification (fast, cheap, sufficient accuracy)
- Batch size of 10 emails per Claude API call (balances latency vs. token cost)
- Body snippets capped at 500 chars to control token usage
- Gmail query targets known ATS domains (greenhouse, lever, workday, etc.) plus job-related subject keywords
