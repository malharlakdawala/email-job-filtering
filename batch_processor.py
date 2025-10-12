"""Batch process emails with progress tracking."""

import logging
from rich.progress import Progress
from classifier import classify_email
from gmail_client import get_emails

logger = logging.getLogger(__name__)


def process_batch(query: str, max_results: int = 100, dry_run: bool = False) -> list[dict]:
    emails = get_emails(query=query, max_results=max_results)
    results = []

    with Progress() as progress:
        task = progress.add_task("Classifying emails...", total=len(emails))

        for email in emails:
            try:
                category = classify_email(email["subject"], email.get("snippet", ""))
                result = {
                    "id": email["id"],
                    "subject": email["subject"],
                    "category": category,
                }
                results.append(result)

                if not dry_run:
                    # Apply label or move to folder
                    pass

            except Exception as e:
                logger.error(f"Failed to classify {email['id']}: {e}")

            progress.advance(task)

    return results
