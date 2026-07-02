import re
from datetime import datetime, timedelta

def resolve_relative_dates(text: str) -> str:
    """
    Scans for relative date/time words in the text and replaces them 
    with actual calculated absolute dates based on today's date.
    Today is assumed to be the system's current date.
    """
    now = datetime.now()
    today_str = now.strftime("%d %B %Y")
    yesterday_str = (now - timedelta(days=1)).strftime("%d %B %Y")
    two_days_ago_str = (now - timedelta(days=2)).strftime("%d %B %Y")

    replacements = {
        r"\byesterday evening\b": f"{yesterday_str}, evening (approximately 19:00)",
        r"\byesterday morning\b": f"{yesterday_str}, morning (approximately 09:00)",
        r"\byesterday afternoon\b": f"{yesterday_str}, afternoon (approximately 14:00)",
        r"\blast night\b": f"{yesterday_str}, night (approximately 22:00)",
        r"\byesterday\b": f"{yesterday_str}",
        r"\bthis morning\b": f"{today_str}, morning (approximately 09:00)",
        r"\btoday morning\b": f"{today_str}, morning (approximately 09:00)",
        r"\bthis afternoon\b": f"{today_str}, afternoon (approximately 14:00)",
        r"\btoday afternoon\b": f"{today_str}, afternoon (approximately 14:00)",
        r"\bthis evening\b": f"{today_str}, evening (approximately 19:00)",
        r"\btoday evening\b": f"{today_str}, evening (approximately 19:00)",
        r"\btonight\b": f"{today_str}, night (approximately 22:00)",
        r"\btoday\b": f"{today_str}",
        r"\btwo days ago\b": f"{two_days_ago_str}"
    }

    processed_text = text
    for pattern, replacement in replacements.items():
        # Case insensitive replacement
        processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)

    return processed_text
