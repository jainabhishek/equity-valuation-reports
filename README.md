# Equity Valuation Reports

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Live site](https://img.shields.io/badge/live%20site-github.io-0a8f86)](https://jainabhishek.github.io/equity-valuation-reports/)
[![As of](https://img.shields.io/badge/as%20of-Aug%208%2C%202026-172033)](#)

Public-information equity research with self-contained HTML memos and live Excel
models. Both packages are designed for hedge-fund PM review: they separate
calculation integrity from trade actionability and recommend no risk until the
evidence and implementation gates clear.

**Live site:** [jainabhishek.github.io/equity-valuation-reports](https://jainabhishek.github.io/equity-valuation-reports/)

## Current memos

| | Alphabet (GOOGL) | Nvidia (NVDA) |
| --- | --- | --- |
| **Stance** | **WAIT FOR PROOF / NO POSITION** | **WATCHLIST / NO POSITION** |
| Market data | $354.24, August 7 regular-hours last trade | $223.90 |
| Primary scenario range | $273.91 / $334.68 / $398.41 | $57.22 / $165.40 / $377.68 |
| Decision reference | **$335.42 (−5.3%)** · illustrative expected value | **$165.40 (−26.1%)** · base DCF, no probabilities |
| Position size | **0.0%** · implementation gates open | **0.0%** · seven gates open |
| Alphabet DCF cross-check | **$143.64** · 90% terminal value, not the catalyst | — |
| Memo | [Open →](https://jainabhishek.github.io/equity-valuation-reports/alphabet/memo.html) | [Open →](https://jainabhishek.github.io/equity-valuation-reports/nvidia/memo.html) |
| Model | [Download](alphabet/model.xlsx) | [Download](nvidia/model.xlsx) |

## Alphabet: selected thesis and decision rule

Alphabet's AI capex may convert into GAAP D&A faster than consensus EPS
incorporates it. The thesis works only if EBITDA fails to absorb the charge,
reported results force FY2027–28 EPS cuts, and the multiple responds. D&A alone
is not the signal, and it is not the direct source of DCF downside because it is
added back in FCFF.

The current result is `WAIT FOR PROOF / 0.0%` because:

- no broker-level quarterly D&A consensus or revision history has been frozen;
- the $15.01 FMP FY2027 EPS snapshot conflicts with a separately cited range;
- no observed print has yet produced the required EPS revision;
- borrow/carry, crowding/squeeze, executable options and hedge inputs are missing;
- the DCF remains dominated by terminal value and is used as a risk frame only.

The conditional initiation rule is explicit: actual D&A must reach or exceed the
frozen path, EBITDA must offset less than half of the surprise, FY2027 consensus
EPS must fall at least 5% within ten trading days, net downside must remain at
least 20%, and every implementation gate must clear.

## Alphabet model architecture

The workbook is a second, formula-driven implementation of the Python model.
Its first visible tab is `Cover`, followed by a source ledger and the calculation
stack:

1. `Sources` separates filed facts, market observations and analyst assumptions.
2. `Drivers` splits FY2026 into reported H1 and forecast H2.
3. `WACC` builds CAPM from the August 7 Treasury rate, beta/ERP assumptions,
   after-tax debt cost and market-value capital weights.
4. `Share Bridge` uses July 15 point-in-time common shares, ordinary dilution and
   full minimum mandatory-convertible dilution. Preferred is not deducted again.
5. `Depreciation` models quarterly capex vintages, asset mix, useful lives and
   commissioning lags. Opening-vintage and forecast-vintage D&A are separate.
6. `Valuation` excludes reported H1, discounts only the August 8 onward stub, and
   normalizes terminal reinvestment using `g / terminal ROIC`.
7. `Variant` carries the consensus conflict and a quarterly catalyst template.
8. `Scenarios`, `Sensitivities`, `Decision` and `Checks` are formula-linked; no
   utility-based sizing or hardcoded position recommendation remains.

The DCF uses explicit haircuts for restricted marketable equity and
non-marketable investments instead of silently treating them as cash. FY2026
capex is $200bn, the midpoint of management's $195–205bn guide; FY2027 is a
visible $230bn analyst assumption, +15%, consistent with management's direction
that spending would increase significantly.

## Nvidia: selected thesis and decision rule

Nvidia's operating results are exceptional; the public-information work does not
establish an investable variant at the August 7 price. The base revenue path is
inside the frozen FY2027 aggregator range. The stock/model disagreement is a
duration argument: spot implies an 8.62% WACC on the base operating path versus
the explicit 10.70% CAPM case, or a blunt 36% uniform uplift to base revenue.
Neither is a differentiated near-term earnings call.

The current result is `WATCHLIST / NO POSITION / 0.0%` because:

- no broker-level consensus cohort or revision history has been frozen;
- customer-financing exposure within $18.6bn of Q1 private investments and
  $27bn of investment commitments is not quantified;
- channel, lead-time, backlog and cancellation evidence is absent;
- Q2 actuals and forward guidance are not filed at this cut;
- live options, short interest, borrow, crowding and portfolio factor data are
  missing; and
- the bear/base/bull DCF states span $57.22 to $377.68.

The conditional rule is symmetric. A long requires observable upside to a
frozen consensus, cleared demand-quality work and at least 20% net underwritten
return. A short requires a reported break in the base path, estimate revisions,
controlled uncapped upside and at least 20% net downside after implementation.

## Nvidia model architecture

The workbook is authored separately with `@oai/artifact-tool` and recalculated
against the Python model. Its 15-sheet stack begins with `Cover`, `Review` and
`Sources`, then carries the calculation and decision layers:

1. `Drivers` distinguishes filed facts, market observations and analyst inputs.
2. `Revenue` anchors FY2027 on Q1 actual revenue and the Q2 guide, and uses
   Nvidia's current Data Center / Edge Computing framework.
3. `WACC` builds CAPM from the 4.65% Treasury, 1.35x beta, 4.50% ERP, after-tax
   debt cost and market-value weights.
4. `Depreciation` separates opening D&A from formula-driven forecast capex
   vintages with short- and long-lived asset buckets.
5. `Equity Bridge` credits cash at par but haircuts public, private and
   equity-method stakes by scenario. Operating leases are disclosed without a
   second deduction from cash flows that already include lease expense.
6. `Valuation` subtracts reported Q1 CFO less capex from FY2027 FCFF and
   normalizes terminal reinvestment with `g / terminal ROIC`.
7. `Scenarios` treats bear, base and bull as unweighted states. No unsupported
   expected value or Kelly sizing remains.
8. `Reverse DCF`, `Sensitivities`, `Decision` and `Checks` expose what spot must
   assume, the duration risk, the seven open capital gates and a forced zero
   position.

The review also corrects the prior memo's Alphabet WACC copy, contradictory
upside language, zeroed Q1 equity-security gains and unsupported claim that the
entire strategic equity portfolio funds customers.

## Alphabet sources

| Need | Source / treatment |
| --- | --- |
| H1 financials, D&A components, balance sheet, shares and preferred mechanics | Alphabet Q2 2026 Form 10-Q and filed earnings release |
| Capex guidance and technical-infrastructure mix | Alphabet Q2 2026 earnings call |
| Asset lives | Alphabet FY2025 Form 10-K |
| Risk-free rate | U.S. Treasury daily yield curve, 4.65% on August 7 |
| Price and 30-day share ADV | Read-only Robinhood quote and fundamentals snapshots |
| FY2027 EPS / EBIT / EBITDA | Frozen FMP aggregator snapshot, explicitly flagged as a source conflict |
| Beta, ERP, terminal ROIC, asset split/lags, probabilities and multiples | Analyst assumptions, labeled at point of use |

The June capital structure is kept precise: 86m common shares and $19.25bn of
mandatory-convertible preferred were issued in June; the $40bn ATM had no sales
through June 30; the August 6 debt filing was preliminary with amounts still
blank as of August 8. Registered but unsold capacity is not described as
authorized capital or inserted into the share count.

## Nvidia sources

| Need | Source / treatment |
| --- | --- |
| Q1 financials, investments, commitments, concentration, D&A and share count | Nvidia Q1 FY2027 Form 10-Q |
| Current reporting framework, Data Center detail and Q2 guide | Nvidia Q1 FY2027 filed earnings release |
| FY2026 historical revenue | Nvidia FY2026 Form 10-K |
| Risk-free rate | U.S. Treasury daily yield curve, 4.65% on August 7 |
| Price | Read-only Robinhood regular-hours snapshot; refresh before risk |
| FY2027–28 revenue consensus | Frozen FMP aggregator snapshot; broker provenance and revisions remain open |
| Beta, ERP, terminal ROIC, asset lives, haircuts and hurdle | Analyst assumptions, labeled at point of use |

## Build and verification

From `build/`:

```bash
python3 alphabet_pm.py              # Alphabet JSON, model and memo
python3 nvidia_pm.py                # Nvidia JSON and memo
node nvidia_workbook.mjs            # Nvidia formula workbook via artifact-tool
python3 render.py                   # Both PM memos
./.venv/bin/python workbook.py      # Both workbooks
./.venv/bin/python previews.py      # landing/social images
./.venv/bin/python verify.py        # independent formula recalculation
```

`verify.py` recalculates both Excel files with a formula engine and compares them
with separate Python implementations. It checks dated FCFF periods, D&A,
capital bridges, WACC, terminal mechanics, scenario values, sensitivity centers,
zero-size gates, sheet architecture and prohibited legacy claims. The Nvidia
workbook is also imported, traced, formula-error scanned and rendered one sheet
at a time with `@oai/artifact-tool` before circulation.

## Known limitations

- No channel checks, expert calls or alternative data.
- No broker-level quarterly D&A consensus, estimate revision history, short
  locate/carry, crowding, live option chain or hedge basis.
- Alphabet's capex asset split, placement lags and opening-vintage runoff are
  estimates; the opening D&A run-rate is held flat because remaining lives by
  historical vintage are not disclosed.
- The Alphabet DCF is highly terminal-sensitive and should not be treated as a
  precise price target.
- Nvidia's FY2027 stub uses reported Q1 CFO less capex as an FCFF proxy; replace
  it with the filed Q2 bridge after results.
- Nvidia's revenue states are consolidated analyst scenarios. The current Data
  Center / Edge framework does not yet have enough reported history for a
  bottom-up forecast.
- Nvidia's DCF is 48%–76% terminal value across states and is a duration risk
  frame, not an executable price target.

Analytical research on public information. Not investment advice, a
recommendation, or a solicitation.
