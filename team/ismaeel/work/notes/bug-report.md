# Bug Report - Week 1

## Backtester Bugs

### Bug 1: Unterminated f-string in Test 1 assert message
- **Found:** 2026-02-12
- **Severity:** Medium
- **Steps to reproduce:**
  1. Open and run `tools/backtester.ipynb`.
  2. Execute the cell labeled "Test 1: Skip-all strategy should return empty DataFrame with correct columns".
- **Expected:** Cell runs and validates empty results columns.
- **Actual:** `SyntaxError: unterminated f-string literal`.
- **Reported to:** James
- **Status:** Open

### Bug 2: Unterminated string in final print cell
- **Found:** 2026-02-12
- **Severity:** Medium
- **Steps to reproduce:**
  1. Open and run `tools/backtester.ipynb`.
  2. Execute the final cell that prints "ALL EDGE CASE TESTS PASSED!".
- **Expected:** Cell prints the pass banner.
- **Actual:** `SyntaxError: unterminated string literal`.
- **Reported to:** James
- **Status:** Open

## Metrics Bugs

- None found so far.

## Passed Tests

| Test | Component | Result |
|------|-----------|--------|
| Backtester notebook execution (post-fix) | Backtester | ✓ Pass |
| Metrics notebook execution | Metrics | ✓ Pass |
