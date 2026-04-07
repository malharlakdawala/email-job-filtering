# Email Job Filtering

A Python CLI tool that automatically filters job application emails in Gmail using Claude AI. It classifies emails into categories (positive, negative, neutral, skip) and organizes your inbox accordingly.

## How It Works

1. Fetches job-related emails from Gmail (targeting ATS domains like Greenhouse, Lever, Workday)
2. Sends batches to Claude for classification
3. Labels positive responses for review, trashes the rest

## Prerequisites

- Python 3.8+
- Google Cloud project with Gmail API enabled and OAuth 2.0 credentials (`credentials.json`)
- Anthropic API key (set as `ANTHROPIC_API_KEY` in `.env`)

## Setup

```bash
pip install -r requirements.txt
```

Place your Google OAuth `credentials.json` in the project root. On first run, you'll authenticate via browser and a `token.json` will be created.

Create a `.env` file:

```
ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
# Dry run - preview classifications without making changes
python filter_emails.py --dry-run --max-emails 10

# Run for real
python filter_emails.py

# Custom options
python filter_emails.py --days 14 --max-emails 50 --label "Jobs/Interesting"
```

## Project Structure

- `filter_emails.py` - Entry point and CLI
- `gmail_client.py` - Gmail API wrapper (OAuth, fetch, label, trash)
- `classifier.py` - Claude-based email classification
- `config.py` - Default constants (query, batch sizes, model)
