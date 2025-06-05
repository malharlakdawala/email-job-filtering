"""Custom email classification categories."""

DEFAULT_CATEGORIES = {
    "application_received": "Application acknowledgement or confirmation",
    "interview_invite": "Interview scheduling or invitation",
    "rejection": "Application rejection or not moving forward",
    "offer": "Job offer or compensation discussion",
    "follow_up": "Follow-up or status update request",
    "recruiter_outreach": "Unsolicited recruiter message",
    "newsletter": "Job board newsletter or digest",
    "other": "Does not fit other categories",
}


def get_categories(custom_file: str | None = None) -> dict:
    categories = dict(DEFAULT_CATEGORIES)
    if custom_file:
        import json
        with open(custom_file) as f:
            custom = json.load(f)
        categories.update(custom)
    return categories


def format_for_prompt(categories: dict) -> str:
    lines = []
    for key, desc in categories.items():
        lines.append(f"- {key}: {desc}")
    return "\n".join(lines)
