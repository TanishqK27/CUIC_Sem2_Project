# Quant Meeting Notes

**Date:** 2026-02-12

Below is a summary of the 12/02/26 thursday meeting

Weekly work is now due on Wednesday evening.
Think, don’t just execute: Question long‑running or inefficient tasks and always keep the overall quant goal (useful data + models) in mind. Raise blockers (e.g. VPN, rate limits) early.
Use AI tools properly: Configure Codex/Claude with project context files, skills (e.g. /context), and a daily /update_log. Read their docs and integrate with GitHub to make them genuinely helpful.
Data pipeline focus: Build and maintain three core NBA datasets (game logs, player stats, team stats) that are comprehensive, centralized, and updated daily, using proxies/IP rotation or similar to avoid slow/blocked scrapes.
GitHub hygiene: At the end of each day, push your branch with clear commit messages and update a short daily log describing what you did, how, and where it lives.
Clear documentation & collaboration: Describe exactly what each module/task does (not just “metrics module built”), offer help when you’re free, and ask for help as soon as you’re blocked.

Validate before scaling: Start with simple, known-outcome strategies to sanity-check the backtest pipeline (columns, empty results, logic) before adding complexity or more data.
Respect real-world frictions: Design strategies with bookie rules, ban risk, max bet limits, and liquidity constraints front of mind; a “profitable” model that can’t be executed is useless.
Execution is part of the model: Treat execution timing, odds movement, and fill quality (especially on live and prediction markets) as core to the strategy, not an afterthought.
Measure liquidity properly: Use sufficiently frequent time-series snapshots and depth information to reason about how much size you can actually get filled at a given price.
Automate where it matters: Use macros / automation to hit target odds and handle fast-changing markets, but keep execution logic transparent and testable.
Collaborate with ownership: Break work into clear sections, assign pairs/owners, and make people responsible for concrete deliverables, not vague “research”.
Surface blockers early: Call out operational blockers (VPN, rate limits, access, data gaps) as soon as they appear so they don’t quietly stall progress.
