# Equity Valuation Reports

Standalone intrinsic-value reports for individual companies, each built as a
self-contained HTML report paired with a formula-driven FCFF DCF workbook.

Valuation date: August 4, 2026.

## Contents

- [`alphabet/`](alphabet/) — Alphabet (GOOGL) intrinsic-value report
- [`nvidia/`](nvidia/) — Nvidia (NVDA) intrinsic-value report

Each company folder contains:

| File | Description |
| --- | --- |
| `report.html` | Primary human-readable deliverable: thesis, operating deep dive, valuation, sources |
| `banker_formula_workbook.xlsx` | Formula-driven FCFF DCF workbook (dashboard, scenarios, reverse DCF, sensitivities, checks, sources) |
| `plan.json` | Normalized DCF plan and assumptions |
| `manifest.json` | Deliverable manifest describing the artifacts in the folder |
| `model_citations.json` | Model-cell citation ledger tying workbook cells back to sources |
| `banker_formula_workbook_run_log.json` | Build/validation run log for the workbook |

`build_reports.py` at the repo root is the generator script used to produce
both reports (six-year FCFF DCF, mid-year convention, Gordon-growth terminal
value; downside/base/upside scenarios; controlled reverse DCFs).

## Methodology notes

- Public filings and reported balance-sheet inputs are sourced; forecasts,
  normalized beta/ERP, and terminal assumptions are independent analyst
  estimates.
- Deliverables are explicitly labeled **screen-grade**, not decision-grade —
  they are a structured starting point for further diligence, not investment
  advice.
- Both DCF plans validate against their JSON schema; workbooks recalculate
  cleanly with zero formula errors; scenario outputs and reverse DCFs tie to
  independent calculations.
