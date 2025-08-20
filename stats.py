"""Email classification statistics and reporting."""

from collections import Counter
from datetime import datetime


class EmailStats:
    def __init__(self):
        self.classifications: list[dict] = []

    def add(self, email_id: str, category: str, subject: str):
        self.classifications.append({
            "email_id": email_id,
            "category": category,
            "subject": subject,
            "classified_at": datetime.now().isoformat(),
        })

    def summary(self) -> dict:
        counts = Counter(c["category"] for c in self.classifications)
        return {
            "total": len(self.classifications),
            "by_category": dict(counts),
            "top_category": counts.most_common(1)[0] if counts else None,
        }

    def format_report(self) -> str:
        s = self.summary()
        lines = [f"Email Classification Report", f"Total: {s['total']} emails\n"]
        for cat, count in sorted(s["by_category"].items(), key=lambda x: -x[1]):
            pct = count / s["total"] * 100 if s["total"] else 0
            lines.append(f"  {cat}: {count} ({pct:.0f}%)")
        return "\n".join(lines)
