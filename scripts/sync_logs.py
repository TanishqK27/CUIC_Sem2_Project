#!/usr/bin/env python3
"""Sync individual team logs to PROJECT_LOG.md.

This script aggregates entries from all team member LOG.md files
into the central PROJECT_LOG.md file.

Usage:
    python scripts/sync_logs.py

    # Or with options:
    python scripts/sync_logs.py --days 7  # Only last 7 days
    python scripts/sync_logs.py --dry-run  # Preview without writing
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path


# Team members (lowercase folder names)
TEAM_MEMBERS = [
    "tan",
    "andrii",
    "dietrich",
    "ben",
    "alfie",
    "max",
    "miran",
    "mya",
    "isameel",
    "vansheeka",
    "james",
]

# Project root (relative to this script)
PROJECT_ROOT = Path(__file__).parent.parent
TEAM_DIR = PROJECT_ROOT / "team"
PROJECT_LOG = TEAM_DIR / "PROJECT_LOG.md"


def parse_log_file(filepath: Path) -> dict[str, list[str]]:
    """Parse a LOG.md file and extract entries by date.

    Args:
        filepath: Path to the LOG.md file.

    Returns:
        Dict mapping date strings to list of entries.
    """
    if not filepath.exists():
        return {}

    content = filepath.read_text()
    entries: dict[str, list[str]] = {}

    current_date = None
    date_pattern = re.compile(r"^###?\s*(\d{4}-\d{2}-\d{2})")

    for line in content.split("\n"):
        # Check for date header
        date_match = date_pattern.match(line)
        if date_match:
            current_date = date_match.group(1)
            if current_date not in entries:
                entries[current_date] = []
            continue

        # Check for bullet point entry
        if current_date and line.strip().startswith("-"):
            entry = line.strip()[1:].strip()  # Remove bullet and whitespace
            if entry:
                entries[current_date].append(entry)

    return entries


def collect_all_entries(
    days: int | None = None,
) -> dict[str, dict[str, list[str]]]:
    """Collect entries from all team members.

    Args:
        days: If set, only include entries from the last N days.

    Returns:
        Dict mapping member names to their entries by date.
    """
    cutoff_date = None
    if days:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    all_entries: dict[str, dict[str, list[str]]] = {}

    for member in TEAM_MEMBERS:
        log_path = TEAM_DIR / member / "LOG.md"
        entries = parse_log_file(log_path)

        # Filter by date if cutoff specified
        if cutoff_date:
            entries = {
                date: items
                for date, items in entries.items()
                if date >= cutoff_date
            }

        if entries:
            all_entries[member] = entries

    return all_entries


def generate_project_log(
    all_entries: dict[str, dict[str, list[str]]],
) -> str:
    """Generate the PROJECT_LOG.md content.

    Args:
        all_entries: Dict of member entries.

    Returns:
        Formatted markdown content.
    """
    # Collect all dates and sort in reverse order
    all_dates: set[str] = set()
    for member_entries in all_entries.values():
        all_dates.update(member_entries.keys())

    sorted_dates = sorted(all_dates, reverse=True)

    # Build the log content
    lines = [
        "# CUIC Quant Fund - Project Log",
        "",
        "Aggregated log of all team member contributions. "
        "Entries are in reverse chronological order (newest first).",
        "",
        "---",
        "",
        "## How to Add Entries",
        "",
        'Use the `/update-log` skill to automatically add entries:',
        "",
        "```",
        "/update-log <your-name> <description of work>",
        "```",
        "",
        "This will update both your personal `team/<name>/LOG.md` and this PROJECT_LOG.md.",
        "",
        "---",
        "",
        "## Log Entries",
        "",
    ]

    for date in sorted_dates:
        lines.append(f"### {date}")
        lines.append("")

        for member in TEAM_MEMBERS:
            if member in all_entries and date in all_entries[member]:
                for entry in all_entries[member][date]:
                    lines.append(f"- **[{member}]** {entry}")

        lines.append("")

    # Footer
    lines.extend([
        "---",
        "",
        "<!-- New entries will be added above this line -->",
    ])

    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync team logs to PROJECT_LOG.md"
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Only include entries from the last N days",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing",
    )
    args = parser.parse_args()

    print("Collecting entries from team logs...")
    all_entries = collect_all_entries(days=args.days)

    # Count entries
    total_entries = sum(
        len(entries)
        for member_entries in all_entries.values()
        for entries in member_entries.values()
    )
    print(f"Found {total_entries} entries from {len(all_entries)} members")

    # Generate new content
    content = generate_project_log(all_entries)

    if args.dry_run:
        print("\n--- DRY RUN - Would write: ---\n")
        print(content)
        print("\n--- END DRY RUN ---")
    else:
        PROJECT_LOG.write_text(content)
        print(f"Updated {PROJECT_LOG}")


if __name__ == "__main__":
    main()
