# Weekly Standup Skill

Generates a weekly progress summary from all team member logs.

## Usage

```
/weekly-standup
```

## No Arguments Required

This skill aggregates data from all team logs automatically.

## Examples

```
/weekly-standup
```

## Instructions

When this skill is invoked with `/weekly-standup`:

1. **Calculate the date range**:
   - End date: Today
   - Start date: 7 days ago
   - Format: YYYY-MM-DD

2. **Read all team LOG.md files**:
   - `team/tan/LOG.md`
   - `team/andrii/LOG.md`
   - `team/dietrich/LOG.md`
   - `team/ben/LOG.md`
   - `team/alfie/LOG.md`
   - `team/max/LOG.md`
   - `team/miran/LOG.md`
   - `team/mya/LOG.md`
   - `team/ismaeel/LOG.md`
   - `team/vansheeka/LOG.md`
   - `team/james/LOG.md`

3. **Extract entries from the past week**:
   - Find date headers (### YYYY-MM-DD) within the date range
   - Collect all bullet points under those dates
   - Associate each entry with the team member's name

4. **Generate the weekly summary** with this format:

```markdown
# Weekly Standup Summary

**Week of:** YYYY-MM-DD to YYYY-MM-DD

---

## Team Activity

### tan
- Entry 1
- Entry 2

### andrii
- Entry 1

### dietrich
*No activity this week*

... (repeat for all members)

---

## Summary Statistics

- **Total entries:** X
- **Active members:** Y / 11
- **Most active:** <name> (Z entries)

---

## Notes

Generated on YYYY-MM-DD HH:MM
```

5. **Present the summary** to the user in the chat

6. **Optionally offer** to append a condensed version to PROJECT_LOG.md

## Output Format

The summary should be formatted as markdown and displayed directly to the user.

## Important Notes

- Include ALL team members, even those with no activity
- Mark inactive members with "*No activity this week*"
- Sort entries chronologically within each member's section
- Calculate accurate statistics
- Date parsing should handle both "### YYYY-MM-DD" and "### Month DD, YYYY" formats
