# Update Log Skill

Updates a team member's personal LOG.md and adds an attributed entry to PROJECT_LOG.md.

## Usage

```
/update-log <name> <message>
```

## Arguments

- `name`: Team member's name (lowercase: tan, andrii, dietrich, ben, alfie, max, miran, mya, isameel, vansheeka, james)
- `message`: Description of work completed

## Examples

```
/update-log tan Completed Polymarket API client implementation
/update-log andrii Added unit tests for Kelly criterion
/update-log mya Fixed bug in arbitrage detection
```

## Instructions

When this skill is invoked with `/update-log <name> <message>`:

1. **Validate the name** - Ensure it matches one of the 11 team members (lowercase):
   - tan, andrii, dietrich, ben, alfie, max, miran, mya, isameel, vansheeka, james
   - If invalid, inform the user and list valid names

2. **Get today's date** in format YYYY-MM-DD

3. **Update personal LOG.md** at `team/<name>/LOG.md`:
   - Find the line `## Log Entries`
   - Check if today's date section exists (### YYYY-MM-DD)
   - If today's section exists, add the message as a new bullet under it
   - If today's section doesn't exist, create it after "## Log Entries" with the message
   - Entry format: `- <message>`

4. **Update PROJECT_LOG.md** at `team/PROJECT_LOG.md`:
   - Find the line `## Log Entries`
   - Check if today's date section exists (### YYYY-MM-DD)
   - If today's section exists, add the attributed entry under it
   - If today's section doesn't exist, create it after "## Log Entries"
   - Entry format: `- **[<name>]** <message>`

5. **Confirm completion** - Tell the user both files have been updated

## File Locations

- Personal log: `team/<name>/LOG.md`
- Project log: `team/PROJECT_LOG.md`

## Template for New Date Section

```markdown
### YYYY-MM-DD

- Entry here
```

## Important Notes

- Always add new entries at the TOP of the log (reverse chronological order)
- New date sections go immediately after "## Log Entries"
- Preserve existing content - only add, never remove
- Use consistent formatting with existing entries
