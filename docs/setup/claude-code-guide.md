# Claude Code Guide

A comprehensive guide to using Claude Code for AI-assisted development in the CUIC Quant Fund project.

---

## Table of Contents

1. [What is Claude Code?](#what-is-claude-code)
2. [Installation](#installation)
3. [Project Configuration](#project-configuration)
4. [Using CLAUDE.md](#using-claudemd)
5. [Custom Skills](#custom-skills)
6. [MCP Servers](#mcp-servers)
7. [IDE Integration](#ide-integration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## What is Claude Code?

**Claude Code** is Anthropic's AI-powered coding assistant that integrates directly into your development workflow. It can:

- Read and understand your entire codebase
- Write, edit, and refactor code
- Run terminal commands
- Search documentation and the web
- Execute multi-step tasks autonomously

### Key Features

| Feature | Description |
|---------|-------------|
| **Context Awareness** | Reads CLAUDE.md and understands project structure |
| **Code Generation** | Writes code following project conventions |
| **File Operations** | Creates, edits, and organizes files |
| **Terminal Access** | Runs commands, tests, and scripts |
| **Custom Skills** | Invoke predefined workflows with `/command` |
| **MCP Integration** | Connect to external tools and data sources |

---

## Installation

### Option 1: VS Code Extension

1. Open VS Code
2. Go to Extensions (Cmd+Shift+X / Ctrl+Shift+X)
3. Search for "Claude Code"
4. Click Install
5. Sign in with your Anthropic account

### Option 2: CLI Tool

```bash
# Install via npm
npm install -g @anthropic-ai/claude-code

# Or via pip
pip install claude-code

# Verify installation
claude --version

# Login
claude login
```

### Option 3: JetBrains IDEs

1. Open PyCharm/IntelliJ
2. Settings → Plugins → Marketplace
3. Search "Claude"
4. Install and restart

---

## Project Configuration

### CLAUDE.md

The `CLAUDE.md` file at the project root provides context to Claude about your project. Claude reads this file automatically when you open the project.

Our `CLAUDE.md` includes:

- Project overview and goals
- Team roster
- Common commands
- Code standards
- Workflow instructions
- Key file locations

### Example Usage

When you ask Claude a question, it uses CLAUDE.md context:

```
You: "How do I run the tests?"

Claude: Based on the project configuration, you can run tests with:
    pytest tests/ -v

For coverage, use:
    pytest tests/ --cov=src/cuic_quant
```

### Checking Status

Use `/status` to verify Claude has loaded the project context:

```
/status

Output:
  Project: CUIC Quant Fund
  CLAUDE.md: Loaded ✓
  Working Directory: /path/to/CUIC_Sem2_Project
  Python: 3.11.0
```

---

## Using CLAUDE.md

### Structure

```markdown
# Project Name

## Overview
Brief description of the project...

## Commands
Common commands for building, testing, etc.

## Code Standards
Formatting, linting, type hints, docstrings...

## Key Files
Important file locations and their purposes...
```

### Updating CLAUDE.md

When adding new patterns or conventions, update CLAUDE.md so Claude follows them:

```markdown
## API Client Pattern

All API clients should:
1. Inherit from `BaseClient`
2. Use `tenacity` for retries
3. Return Pydantic models
4. Include comprehensive docstrings

Example:
```python
class NewClient(BaseClient):
    def get_data(self) -> DataModel:
        ...
```

---

## Custom Skills

Skills are predefined workflows invoked with `/skill-name`. This project includes three custom skills.

### /update-log

Updates your personal LOG.md and the project-wide PROJECT_LOG.md.

**Usage:**
```
/update-log tan Completed Polymarket API client implementation
```

**What it does:**
1. Adds timestamped entry to `team/tan/LOG.md`
2. Adds attributed entry to `team/PROJECT_LOG.md`

### /research-template

Creates a new research notebook from the template.

**Usage:**
```
/research-template polymarket market-efficiency
```

**Arguments:**
- Category: `polymarket`, `kalshi`, `sports`, or `exploratory`
- Name: Notebook name (kebab-case)

**What it does:**
1. Copies `research/notebooks/templates/research_template.ipynb`
2. Saves to `research/notebooks/<category>/<name>.ipynb`
3. Updates notebook metadata

### /weekly-standup

Generates a weekly summary from all team logs.

**Usage:**
```
/weekly-standup
```

**What it does:**
1. Reads all `team/<name>/LOG.md` files
2. Extracts entries from the past week
3. Generates formatted summary
4. Optionally appends to PROJECT_LOG.md

### Creating New Skills

Skills are defined in `.claude/skills/<skill-name>/SKILL.md`:

```markdown
---
name: my-skill
description: Does something useful
arguments:
  - name: arg1
    description: First argument
    required: true
---

# Instructions

When this skill is invoked:

1. First, do this
2. Then, do that
3. Finally, complete with this

## Example

Input: /my-skill value1
Output: Expected behavior
```

---

## MCP Servers

MCP (Model Context Protocol) servers extend Claude's capabilities by connecting to external tools and data sources.

### Project MCP Configuration

The `.mcp.json` file configures project-scoped MCP servers:

```json
{
  "servers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/context7-mcp-server"]
    }
  }
}
```

### Available MCP Servers

| Server | Purpose | Usage |
|--------|---------|-------|
| **context7** | Library documentation | Ask about any library |
| **filesystem** | Enhanced file operations | File management |
| **git** | Git operations | Version control |
| **web** | Web browsing | Research and docs |

### Using MCP Tools

MCP servers provide tools Claude can use automatically:

```
You: "How do I use pandas to resample time series data?"

Claude: [Uses context7 to fetch pandas documentation]

Based on the pandas documentation, you can resample time series with:

    df.resample('1h').mean()

Here's a complete example for our use case...
```

### Adding MCP Servers

Edit `.mcp.json` to add new servers:

```json
{
  "servers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "env": {
        "API_KEY": "${MY_API_KEY}"
      }
    }
  }
}
```

---

## IDE Integration

### VS Code

#### Setup

1. Install Claude Code extension
2. Open project folder
3. Claude automatically reads CLAUDE.md

#### Using Claude in VS Code

- **Chat Panel**: Cmd+Shift+P → "Claude: Open Chat"
- **Inline Suggestions**: Type and Claude suggests
- **Quick Fix**: Hover on error → Claude fix suggestion
- **Terminal**: Run commands through Claude

#### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Shift+P` | Command palette |
| `Cmd+K` | Quick action |
| `Cmd+Enter` | Send message |

### PyCharm

#### Setup

1. Install Claude plugin
2. Open project
3. Configure in Settings → Tools → Claude

#### Features

- Code completion
- Refactoring assistance
- Documentation generation
- Test generation

---

## Best Practices

### 1. Be Specific

```
# Good
"Create a function that converts American odds to decimal odds,
with type hints and Google-style docstring, following our project conventions."

# Less Good
"Write an odds converter"
```

### 2. Provide Context

```
# Good
"Looking at src/cuic_quant/data/polymarket_client.py, add a method to
fetch historical prices for a market. It should follow the same pattern
as get_markets()."

# Less Good
"Add historical prices method"
```

### 3. Review Generated Code

Always review Claude's output:

- [ ] Does it follow project conventions?
- [ ] Are there type hints?
- [ ] Is the docstring correct?
- [ ] Are edge cases handled?
- [ ] Would you write it differently?

### 4. Iterate

```
You: "Create a Kelly criterion function"
Claude: [Generates function]
You: "Add input validation and handle edge cases"
Claude: [Updates function]
You: "Add unit tests for this function"
Claude: [Generates tests]
```

### 5. Use Skills for Repetitive Tasks

Instead of manually:
```
You: "Add an entry to my log saying I completed the API client"
```

Use the skill:
```
/update-log tan Completed Polymarket API client
```

### 6. Keep CLAUDE.md Updated

When you establish new patterns, add them to CLAUDE.md so Claude follows them consistently.

---

## Troubleshooting

### Claude Doesn't See My Files

```
# Check status
/status

# If CLAUDE.md not loaded, refresh
/refresh
```

### Claude Doesn't Follow Conventions

1. Check CLAUDE.md has the convention documented
2. Explicitly reference it: "Following our project conventions in CLAUDE.md..."
3. Provide an example of what you want

### MCP Server Not Working

```bash
# Check server status
claude mcp status

# Restart servers
claude mcp restart

# Check logs
claude mcp logs context7
```

### Skills Not Found

```
# List available skills
/help

# Check skill file exists
ls -la .claude/skills/
```

### Performance Issues

- Large files may slow responses
- Use specific file references instead of "look at the whole codebase"
- Break complex tasks into smaller steps

---

## Example Workflows

### Adding a New API Client

```
1. /research-template exploratory new-api-exploration

2. You: "Based on the Polymarket client pattern in
   src/cuic_quant/data/polymarket_client.py, create a
   client for the XYZ API. Their base URL is api.xyz.com
   and they use bearer token auth."

3. Review and iterate on the generated code

4. You: "Add unit tests for this client following our test patterns"

5. /update-log tan Created XYZ API client with tests
```

### Debugging an Issue

```
1. You: "I'm getting a KeyError when fetching market data.
   Here's the traceback: [paste traceback]"

2. Claude: [Analyzes code and suggests fix]

3. You: "Apply the fix and add a test case for this edge case"

4. Run tests: pytest tests/ -v
```

### Research Workflow

```
1. /research-template polymarket market-efficiency

2. Open notebook, write hypothesis

3. You: "Help me write code to fetch the last 30 days of price data
   for the top 10 Polymarket markets by volume"

4. Analyze results, document findings

5. /update-log tan Completed market efficiency analysis for Polymarket
```

---

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [VS Code Extension Guide](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code)
- [CLAUDE.md Best Practices](https://docs.anthropic.com/claude-code/claude-md)

---

## Next Steps

1. Try `/status` to verify setup
2. Use `/update-log` to add your first entry
3. Create a research notebook with `/research-template`
4. Review [Environment Setup](environment-setup.md) if needed
