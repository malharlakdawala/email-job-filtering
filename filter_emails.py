#!/usr/bin/env python3
"""Gmail job application email filter.

Classifies job-related emails using Claude AI and takes action:
- POSITIVE (interviews, shortlisted, tasks) → labeled for review
- NEGATIVE (rejections) → trashed
- NEUTRAL (acknowledgments) → trashed
- SKIP (not job-related) → left alone
"""

import argparse
import sys
import time

from dotenv import load_dotenv
load_dotenv()

from config import (
    GMAIL_QUERY,
    GMAIL_LABEL_NAME,
    MAX_EMAILS_PER_RUN,
    CLASSIFICATION_BATCH_SIZE,
)
from gmail_client import (
    get_gmail_service,
    list_messages,
    get_message_details,
    ensure_label,
    trash_messages,
    label_messages,
)
from classifier import classify_emails


def parse_args():
    parser = argparse.ArgumentParser(
        description="Filter job application emails in Gmail using Claude AI."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without modifying any emails.",
    )
    parser.add_argument(
        "--max-emails",
        type=int,
        default=MAX_EMAILS_PER_RUN,
        help=f"Maximum emails to process (default: {MAX_EMAILS_PER_RUN}).",
    )
    parser.add_argument(
        "--label",
        default=GMAIL_LABEL_NAME,
        help=f'Gmail label for positive emails (default: "{GMAIL_LABEL_NAME}").',
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Override newer_than period in days (default: from config query).",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Override the entire Gmail search query.",
    )
    return parser.parse_args()


def build_query(args):
    if args.query:
        return args.query
    query = GMAIL_QUERY
    if args.days:
        # Replace newer_than:Xd in the default query
        import re
        query = re.sub(r"newer_than:\d+d", f"newer_than:{args.days}d", query)
    # Exclude already-labeled emails
    query += f' -label:{args.label.replace("/", "-").replace(" ", "-").lower()}'
    return query


def main():
    args = parse_args()

    if args.dry_run:
        print("=== DRY RUN MODE (no emails will be modified) ===\n")

    # Step 1: Authenticate
    print("Authenticating with Gmail...")
    service = get_gmail_service()

    # Step 2: Ensure label exists
    label_id = ensure_label(service, args.label)
    print(f'Using label: "{args.label}"\n')

    # Step 3: Fetch emails
    query = build_query(args)
    print(f"Searching emails with query:\n  {query}\n")
    messages = list_messages(service, query, args.max_emails)

    if not messages:
        print("No matching emails found. Nothing to do.")
        return

    print(f"Found {len(messages)} emails to process.\n")

    # Step 4: Process in batches
    counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0, "SKIP": 0}
    total_processed = 0

    msg_ids = [m["id"] for m in messages]

    for i in range(0, len(msg_ids), CLASSIFICATION_BATCH_SIZE):
        batch_ids = msg_ids[i : i + CLASSIFICATION_BATCH_SIZE]
        batch_num = (i // CLASSIFICATION_BATCH_SIZE) + 1
        total_batches = (len(msg_ids) + CLASSIFICATION_BATCH_SIZE - 1) // CLASSIFICATION_BATCH_SIZE
        print(f"--- Batch {batch_num}/{total_batches} ({len(batch_ids)} emails) ---")

        # Fetch details
        emails = []
        for msg_id in batch_ids:
            details = get_message_details(service, msg_id)
            emails.append(details)

        # Classify
        try:
            classifications = classify_emails(emails)
        except Exception as e:
            import traceback
            print(f"  Classification error: {e}")
            traceback.print_exc()
            print("  Skipping batch.")
            continue

        # Build lookup for actions
        class_map = {c["id"]: c["category"] for c in classifications}

        to_trash = []
        to_label = []

        for email in emails:
            category = class_map.get(email["id"], "SKIP")
            counts[category] = counts.get(category, 0) + 1
            total_processed += 1

            status_icon = {
                "POSITIVE": "+",
                "NEGATIVE": "-",
                "NEUTRAL": "~",
                "SKIP": "?",
            }.get(category, "?")

            print(f"  [{status_icon}] {category:8s} | {email['subject'][:60]}")

            if category in ("NEGATIVE", "NEUTRAL"):
                to_trash.append(email["id"])
            elif category == "POSITIVE":
                to_label.append(email["id"])

        # Take action
        if not args.dry_run:
            if to_trash:
                trash_messages(service, to_trash)
            if to_label:
                label_messages(service, to_label, label_id)
        else:
            if to_trash:
                print(f"  (would trash {len(to_trash)} emails)")
            if to_label:
                print(f"  (would label {len(to_label)} emails)")

        print()

        # Small delay between batches to avoid rate limits
        if i + CLASSIFICATION_BATCH_SIZE < len(msg_ids):
            time.sleep(0.5)

    # Step 5: Summary
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"  Total processed:      {total_processed}")
    print(f"  Positive (labeled):   {counts['POSITIVE']}")
    print(f"  Negative (trashed):   {counts['NEGATIVE']}")
    print(f"  Neutral  (trashed):   {counts['NEUTRAL']}")
    print(f"  Skipped:              {counts['SKIP']}")
    if args.dry_run:
        print("\n  (Dry run — no emails were modified)")


if __name__ == "__main__":
    main()
