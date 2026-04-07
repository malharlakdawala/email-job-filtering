import json
import re

import anthropic

from config import CLAUDE_MODEL

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an email classifier for job application emails. Classify each email into exactly one category:

- POSITIVE: Interview invitations, shortlisted notifications, recruiter outreach wanting to schedule a call/interview, offer letters, next steps in hiring process, assignment/task sharing, requests to submit a video resume or video introduction, take-home assessments, coding challenges, or any email asking the user to complete something as part of a job application. These emails require the user's DIRECT action toward getting a job. Be strict — only mark as POSITIVE if the email clearly advances the user in a hiring process.
- NEGATIVE: Rejections, "we decided to move forward with other candidates", position filled, application closed.
- NEUTRAL: Application confirmations, "thank you for applying", "we received your application", generic acknowledgments, surveys, feedback requests, satisfaction questionnaires, NPS scores, "how was your experience" emails, newsletter/marketing emails, promotional emails, event invitations, webinar invites, job alerts/recommendations, and any email that does NOT require direct action toward a specific job application.
- SKIP: Not a job-related email, or too ambiguous to classify confidently.

You MUST respond with ONLY a JSON object (no markdown, no code blocks, no extra text). The JSON must have a "classifications" array where each element has "id" (the email ID provided) and "category" (one of: POSITIVE, NEGATIVE, NEUTRAL, SKIP).

Example response:
{"classifications": [{"id": "abc123", "category": "NEGATIVE"}, {"id": "def456", "category": "POSITIVE"}]}"""


def _extract_json(text):
    """Extract JSON from response, handling markdown code blocks."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1).strip())

    # Try finding first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])

    raise ValueError(f"Could not extract JSON from response:\n{text[:500]}")


def classify_emails(emails):
    """Classify a batch of emails using Claude API.

    Args:
        emails: list of dicts with keys: id, from, subject, body_snippet

    Returns:
        list of dicts with keys: id, category
    """
    if not emails:
        return []

    # Format emails for the prompt
    parts = ["Classify these emails:\n"]
    for email in emails:
        parts.append(
            f'[EMAIL id="{email["id"]}"]\n'
            f'From: {email["from"]}\n'
            f'Subject: {email["subject"]}\n'
            f'Body: {email["body_snippet"]}\n'
            f"[/EMAIL]\n"
        )
    user_message = "\n".join(parts)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text
    parsed = _extract_json(text)
    return parsed["classifications"]
