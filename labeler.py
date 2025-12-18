"""Gmail label management for classified emails."""

import logging
from gmail_client import get_service

logger = logging.getLogger(__name__)

LABEL_PREFIX = "AI-Classified"


def ensure_labels_exist(categories: list[str]) -> dict[str, str]:
    """Create Gmail labels for each category, return name->id mapping."""
    service = get_service()
    existing = service.users().labels().list(userId="me").execute()
    label_map = {l["name"]: l["id"] for l in existing.get("labels", [])}

    created = {}
    for category in categories:
        label_name = f"{LABEL_PREFIX}/{category}"
        if label_name in label_map:
            created[category] = label_map[label_name]
        else:
            result = service.users().labels().create(
                userId="me",
                body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"},
            ).execute()
            created[category] = result["id"]
            logger.info(f"Created label: {label_name}")

    return created


def apply_label(email_id: str, label_id: str):
    service = get_service()
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"addLabelIds": [label_id]},
    ).execute()
