# Team Standard Operating Procedures

## SOP 1: CSV Handoff to Dietrich

**Who:** Anyone producing data CSVs
**When:** Before sending any CSV to Dietrich

1. Check your CSV matches format in `docs/reference/csv-formats.md`
2. Run Max's validator: `python scripts/validate_csv.py <type> <path>`
3. If FAIL: fix issues, do NOT send to Dietrich
4. If PASS: message Max confirming CSV is ready
5. Max gives final OK, then send to Dietrich
6. Dietrich loads — he does NOT fix your CSV errors

**Dietrich's rule:** Wrong format = sent back. Fix it yourself.

---

## SOP 2: Bug Reporting

**Who:** Anyone who finds a bug
**When:** Immediately upon finding

1. Stop what you're doing
2. Write down EXACT steps to reproduce
3. Note expected vs actual behavior
4. Tell the code owner directly (Slack/Discord)
5. Add to your `work/notes/` bug log
6. Do NOT try to fix someone else's code

**Format:**
```
Bug: [one line description]
Steps: 1. ... 2. ... 3. ...
Expected: ...
Actual: ...
```

---

## SOP 3: Blocker Escalation

**Who:** Anyone stuck
**When:** Before asking Tan

1. Google the error message (10 min)
2. Ask Claude/ChatGPT (10 min)
3. Check internal docs in `docs/` (5 min)
4. Ask your direct collaborator (see your task brief)
5. Post in team chat with what you tried
6. **ONLY THEN** ask Tan

**When messaging about blockers, include:**
- What you're trying to do
- What you tried
- The exact error/issue

---

## SOP 4: Daily Updates

**Who:** Everyone
**When:** End of each day (5pm)

Update your `team/<name>/LOG.md`:
```markdown
### YYYY-MM-DD
- What I did today
- Blockers (if any)
- Tomorrow's plan
```

---

## SOP 5: Thursday Presentations

**Who:** Everyone
**When:** Thursday meetings

**Format:**
1. Screen share your deliverable
2. Demo it working (not slides)
3. State any blockers
4. **MAX 2 minutes** (Tan will cut you off)

**Do NOT:**
- Make slides
- Explain theory
- Ask questions (save for after)
- Go over time

---

## SOP 6: Code Handoffs

**Who:** Anyone whose code others depend on
**When:** Before someone else uses your code

1. Ensure code runs without errors
2. Add basic docstring/comments
3. Test with sample data
4. Tell the dependent person it's ready
5. Be available for questions that day

---

## SOP 7: Working with Railway DB

**Who:** Anyone querying the database
**When:** Always

```python
import os
from sqlalchemy import create_engine

# ALWAYS use environment variable
engine = create_engine(os.environ['DATABASE_URL'])

# NEVER hardcode credentials
# NEVER commit DATABASE_URL to git
```

Get DATABASE_URL from Dietrich or `configs/.env.example`

---

## SOP 8: Git Commits

**Who:** Everyone with code tasks
**When:** End of each work session

```bash
git add <specific files>  # NOT git add .
git commit -m "feat: short description"
git push origin main
```

**Commit message format:**
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` tests

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| CSV ready | Validate → Max → Dietrich |
| Found bug | Document → Tell owner |
| Stuck | Google → AI → Docs → Teammate → Chat → Tan |
| End of day | Update LOG.md |
| Thursday | 2 min demo, no slides |
| Code ready | Test → Document → Notify dependent |
