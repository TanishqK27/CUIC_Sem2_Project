# Research Template Skill

Creates a new research notebook from the project template.

## Usage

```
/research-template <category> <name>
```

## Arguments

- `category`: One of `polymarket`, `kalshi`, `sports`, or `exploratory`
- `name`: Notebook name in kebab-case (e.g., `market-efficiency`, `arbitrage-detection`)

## Examples

```
/research-template polymarket market-efficiency
/research-template kalshi weather-contracts
/research-template sports nba-over-under
/research-template exploratory cross-market-correlation
```

## Instructions

When this skill is invoked with `/research-template <category> <name>`:

1. **Validate the category** - Must be one of:
   - `polymarket`
   - `kalshi`
   - `sports`
   - `exploratory`
   - If invalid, inform the user and list valid categories

2. **Validate the name**:
   - Should be kebab-case (lowercase with hyphens)
   - No spaces or special characters
   - Convert if needed (e.g., "Market Efficiency" → "market-efficiency")

3. **Check for existing notebook**:
   - Path: `research/notebooks/<category>/<name>.ipynb`
   - If exists, warn user and ask for confirmation or alternative name

4. **Read the template**:
   - Source: `research/notebooks/templates/research_template.ipynb`

5. **Create the new notebook**:
   - Destination: `research/notebooks/<category>/<name>.ipynb`
   - Update the notebook metadata:
     - Title: Convert kebab-case to Title Case
     - Category: The provided category
     - Date: Today's date
     - Author: (leave as placeholder for user to fill)

6. **Update the first markdown cell** with:
   - Title matching the name
   - Category
   - Creation date
   - Placeholder for author

7. **Confirm creation**:
   - Tell user the file was created
   - Provide the full path
   - Suggest opening in Jupyter: `jupyter lab research/notebooks/<category>/<name>.ipynb`

## Directory Structure

```
research/notebooks/
├── templates/
│   └── research_template.ipynb
├── polymarket/
│   └── <notebooks>
├── kalshi/
│   └── <notebooks>
├── sports/
│   └── <notebooks>
└── exploratory/
    └── <notebooks>
```

## Template Modifications

When copying the template, make these changes:

1. **Cell 1 (Markdown - Title)**:
   ```markdown
   # <Title Case Name>

   **Category:** <category>
   **Created:** <YYYY-MM-DD>
   **Author:** [Your Name]

   ## Abstract

   Brief description of this research...
   ```

2. **Metadata** (if present in notebook JSON):
   ```json
   {
     "cuic_quant": {
       "category": "<category>",
       "name": "<name>",
       "created": "<YYYY-MM-DD>"
     }
   }
   ```

## Important Notes

- Create parent directories if they don't exist
- Preserve all template cells and structure
- Only modify the title/metadata cells
- Keep the template file unchanged
