# Alphabet PM-ready memo and model

## Objective

Remediate the reviewed Alphabet memo and workbook so the package is safe to circulate to a long/short hedge-fund PM. The finished package must distinguish calculation integrity from investment actionability, keep the model and memo synchronized, and recommend no risk until the evidence and implementation gates required for a short are cleared.

## Scope

- Rebuild the Alphabet DCF around a valuation-date stub instead of discounting a full 2026 cash flow from a June balance sheet.
- Replace the hardcoded D&A path with a formula-driven placed-in-service schedule anchored to reported H1 D&A, management's disclosed capex mix, explicit useful lives, and deployment lags.
- Normalize terminal cash flow to terminal growth and ROIC.
- Replace the quarterly weighted-average diluted share denominator with a point-in-time share bridge and consistent preferred-stock treatment.
- Build WACC visibly from CAPM and debt inputs, with source and assumption labels.
- Make scenarios, variants, expected value, sensitivities, readiness, and decision outputs live in the workbook.
- Reframe the memo from an actionable 5% short to a conditional `WAIT FOR PROOF / NO POSITION` posture unless trade-implementation gates are supported.
- Add a source ledger, checks, direct citations, monitoring triggers, and a causal EPS-revision-to-stock framework.
- Refresh repository summaries and preview artifacts so nothing contradicts the revised package.

## Progress

- [x] Reproduce the prior PM/model review findings and inspect the current workbook visually.
- [x] Confirm the repository has no local `PLANS.md`; use this checked-in plan as the fallback described by the workspace instructions.
- [x] Finalize the remediation architecture and primary-source fact set.
- [x] Implement model-engine, decision-layer, workbook, and memo changes.
- [x] Regenerate Alphabet outputs and dependent site/README artifacts.
- [x] Run formula, source, visual, and PM-circulation QA.
- [x] Commit, push, and open a pull request.

## Implementation decisions

1. **Two readiness labels.** `Calculation integrity` can pass while `Trade implementation` remains open. The recommendation remains zero risk until borrow/carry, crowding/squeeze, live options, and hedge inputs are verified.
2. **Conditional thesis.** The memo will not claim that the D&A schedule itself creates DCF downside. It will present D&A as a potential estimate-revision catalyst and the DCF as a separate valuation/risk frame.
3. **Point-in-time valuation.** Forecast 2026 will be split into reported H1 and a remaining stub. Discount exponents will be explicit fractions from the valuation date rather than `i + 0.5`.
4. **Placed-in-service D&A.** The model will use a visible quarterly schedule, starting from reported H1 D&A and Q2 run-rate, then allocate forecast capex to servers/machines, networking, and buildings with separate lives and deployment lags.
5. **Normalized terminal value.** Terminal FCFF will equal next-period NOPAT less growth-required reinvestment (`g / terminal ROIC * NOPAT`), with blocking controls for unstable WACC/g and implausible ROIC/reinvestment.
6. **No Kelly sizing.** The invalid Kelly calculation will be removed. The decision layer will show a zero current position and an implementation-gate table; any future conditional size will be governed by loss budget, liquidity, squeeze, hedge, and concentration constraints.
7. **Existing surfaces preserved.** The user explicitly asked to update the existing package, so `alphabet/memo.html` and `alphabet/model.xlsx` remain the reader-facing deliverables.

## Validation

- Model engine and workbook output tie for every explicit FCFF period, enterprise value, equity value, value/share, scenario value, expected value, and terminal-value share.
- Workbook has no formula errors, external links, circular references, hardcoded decision outputs, or stale D&A/variant/scenario tables.
- Sources and assumptions are visible at the point of use and in a dedicated source ledger.
- Desktop and narrow-screen memo screenshots show no clipping or page-level horizontal overflow.
- Every workbook sheet is rendered and inspected; key formulas and source cells are traced.
- Repository tests/build checks pass, and the worktree contains only intended changes before commit.

## Known blockers and posture

- Broker-level consensus D&A, executable borrow/carry, crowding, option-chain, and hedge inputs are not present in the repository. Unless a callable source supplies them, the package will state that they are missing and keep the action at `WAIT FOR PROOF / 0%` rather than inventing values.
- The repository's historical workbook generator uses a Python Excel library. The final workbook will also be imported, recalculated, rendered, and exported through the bundled spreadsheet runtime so the delivered artifact is independently verified.

## Outcome and evidence

- The reader-facing decision is `WAIT FOR PROOF / NO POSITION`, with a current size of `0.0%` and explicit conditional initiation, add, stand-down, implementation, and hedge rules.
- Primary valuation uses FY2027 EPS multiplied by case-specific exit multiples: $273.91 bear, $334.68 base, and $398.41 bull. Probability-weighted value is $335.42, 5.3% below the August 7 spot price; it is labeled illustrative and does not create a trade recommendation.
- The $143.64 DCF is retained only as a risk cross-check. It uses a dated 2026 stub, a formula-built 8.81% WACC, normalized terminal reinvestment, and a point-in-time diluted share bridge; its 89.9% terminal-value share is disclosed prominently.
- The consensus control failure is explicit: the frozen $15.01 FMP FY2027 EPS is above a separately cited $14.20-$14.68 range. The legacy 5% acceptance tolerance was removed so a future generic build fails rather than silently endorsing the mismatch.
- FY2026 capex is $200bn, the midpoint of the latest $195-$205bn guide. FY2027 capex is a clearly labeled $230bn analyst assumption, consistent with management's directional expectation of a significant increase and no longer tripping its own kill criterion.
- The workbook contains 14 visible, ordered sheets from `Cover` through `Notes`; scenarios, D&A, WACC, share bridge, valuation, sensitivity, decision, and checks are formula-linked.
- The independent spreadsheet runtime found no formula errors after import/export. The formula verifier passed 71 Python/workbook tie-outs, including all six FCFF periods, scenario targets, point shares, WACC, terminal value, and PM gating.
- Desktop and narrow-screen browser QA passed without clipping or page-level overflow. Every workbook sheet was rendered, with Cover, Depreciation, Valuation, and Decision inspected at full resolution.
- Robinhood was used read-only for the August 7 GOOGL quote and 30-day ADV. No account data was accessed and no trade was placed.
