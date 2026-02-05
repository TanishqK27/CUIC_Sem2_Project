# Git Workflow Guide

Standard operating procedure for development using Git and GitHub.

---

## Overview

We use a **feature branch workflow**:

1. Create a branch for your work
2. Make commits on your branch
3. Push to GitHub
4. Open a Pull Request (PR)
5. Get review and merge

**Never commit directly to `main`.**

---

## Quick Reference

```bash
# Start new work
git checkout main
git pull origin main
git checkout -b <your-name>/<feature-name>

# Save your work
git add <files>
git commit -m "description of changes"

# Push to GitHub
git push -u origin <your-name>/<feature-name>

# Create PR on GitHub or use:
gh pr create
```

---

## Step-by-Step Guide

### 1. Start Fresh from Main

Before starting new work, make sure you have the latest code:

```bash
git checkout main
git pull origin main
```

### 2. Create Your Branch

Branch names follow the pattern: `<your-name>/<feature-description>`

```bash
# Examples:
git checkout -b alfie/oddsharvester-client
git checkout -b max/sports-odds-repository
git checkout -b tan/fix-polymarket-bug
```

**Branch naming conventions:**

- Use lowercase
- Use hyphens, not spaces or underscores
- Keep it short but descriptive
- Prefix with your name

### 3. Make Changes and Commit

Work on your code, then stage and commit:

```bash
# See what changed
git status

# Stage specific files (preferred)
git add src/cuic_quant/data/new_file.py
git add tests/test_new_file.py

# Or stage all changes (use carefully)
git add .

# Commit with a clear message
git commit -m "feat: add OddsHarvester client wrapper"
```

**Commit message format:**

```
<type>: <short description>

<optional longer description>
```

Types:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding tests
- `refactor:` - Code change that doesn't add feature or fix bug

### 4. Push to GitHub

First time pushing a branch:

```bash
git push -u origin alfie/oddsharvester-client
```

Subsequent pushes:

```bash
git push
```

### 5. Create a Pull Request

**Option A: GitHub website**

1. Go to the repository on GitHub
2. Click "Compare & pull request" (appears after you push)
3. Fill in title and description
4. Click "Create pull request"

**Option B: GitHub CLI**

```bash
gh pr create --title "Add OddsHarvester client" --body "Description of changes"
```

### 6. Code Review

- Request review from Tan or another team member
- Address any feedback with new commits
- Push updates to the same branch

### 7. Merge

Once approved:

- Click "Merge pull request" on GitHub
- Delete the branch after merging (GitHub offers this option)

Locally, clean up:

```bash
git checkout main
git pull origin main
git branch -d alfie/oddsharvester-client  # delete local branch
```

---

## Common Scenarios

### Updating Your Branch with Latest Main

If `main` has been updated while you're working:

```bash
git checkout main
git pull origin main
git checkout your-branch
git merge main
# Resolve any conflicts if needed
git push
```

### Undoing Changes

```bash
# Discard uncommitted changes to a file
git checkout -- filename.py

# Undo last commit but keep changes
git reset --soft HEAD~1

# Discard all uncommitted changes (careful!)
git checkout .
```

### Checking What's Different

```bash
# See uncommitted changes
git diff

# See what's in your branch vs main
git diff main...your-branch

# See commit history
git log --oneline -10
```

### Stashing Work Temporarily

Need to switch branches but have uncommitted work?

```bash
# Save work temporarily
git stash

# Switch branches, do other work...
git checkout main

# Come back and restore
git checkout your-branch
git stash pop
```

---

## PR Best Practices

### Good PR Title

```
feat: add OddsHarvester client for sports odds scraping
```

### Good PR Description

```markdown
## Summary
- Added `OddsHarvesterClient` class that wraps the CLI tool
- Parses JSON output into dataclasses
- Includes retry logic for failed scrapes

## Testing
- Added unit tests in `tests/test_oddsharvester.py`
- Manually tested with NBA historical data

## Related
- Closes #12
- Part of TASK-026
```

### PR Checklist

Before requesting review:

- [ ] Code runs without errors
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Linting passes (`ruff check src/`)
- [ ] Updated relevant documentation
- [ ] Commit messages are clear

---

## Branch Protection

The `main` branch is protected:

- Cannot push directly to main
- PRs require at least 1 approval
- All checks must pass before merging

---

## Getting Help

```bash
# See available commands
git help

# Get help on specific command
git help commit

# See current state
git status

# See branch info
git branch -a
```

If you're stuck, ask in the team chat or ping Tan.

---

## Cheat Sheet

| Task | Command |
|------|---------|
| Start new branch | `git checkout -b name/feature` |
| See changes | `git status` |
| Stage files | `git add <files>` |
| Commit | `git commit -m "message"` |
| Push new branch | `git push -u origin branch-name` |
| Push updates | `git push` |
| Switch branch | `git checkout branch-name` |
| Update from main | `git pull origin main` |
| Create PR | `gh pr create` |
| See branches | `git branch -a` |
| Delete local branch | `git branch -d branch-name` |
