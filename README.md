# Equity Valuation Reports

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Live site](https://img.shields.io/badge/live%20site-github.io-0a8f86)](https://jainabhishek.github.io/equity-valuation-reports/)
[![As of](https://img.shields.io/badge/as%20of-Aug%208%2C%202026-172033)](#)

Public-information equity research with self-contained HTML memos and live Excel
models. The current Alphabet package is designed for hedge-fund PM review: it
separates calculation integrity from trade actionability and recommends no risk
until the evidence and implementation gates clear.

**Live site:** [jainabhishek.github.io/equity-valuation-reports](https://jainabhishek.github.io/equity-valuation-reports/)

## Current memos

| | Alphabet (GOOGL) | Nvidia (NVDA) |
| --- | --- | --- |
| **Stance** | **WAIT FOR PROOF / NO POSITION** | **NO POSITION** |
| Market data | $354.24, August 7 regular-hours last trade | $223.90 |
| Primary scenario range | $273.91 / $334.68 / $398.41 | $67.39 / $197.39 / $437.47 |
| Probability-weighted value | **$335.42 (−5.3%)** · illustrative only | **$224.91 (+0.5%)** |
| Position size | **0.0%** · implementation gates open | **0.0%** |
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

## Sources

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

## Build and verification

From `build/`:

```bash
python3 alphabet_pm.py              # Alphabet JSON, model and memo
python3 render.py                   # Alphabet PM memo + Nvidia memo
./.venv/bin/python workbook.py      # Alphabet PM workbook + Nvidia workbook
./.venv/bin/python previews.py      # landing/social images
./.venv/bin/python verify.py        # independent formula recalculation
```

`verify.py` recalculates the Excel files with a formula engine and currently
checks 71 items: Alphabet's dated FCFF periods, WACC, point-in-time shares,
terminal mechanics, scenario targets, expected value, formula architecture,
sensitivity center, zero-size gate and prohibited legacy claims, plus Nvidia's
existing model tie-outs.

## Known limitations

- No channel checks, expert calls or alternative data.
- No broker-level quarterly D&A consensus, estimate revision history, short
  locate/carry, crowding, live option chain or hedge basis.
- Alphabet's capex asset split, placement lags and opening-vintage runoff are
  estimates; the opening D&A run-rate is held flat because remaining lives by
  historical vintage are not disclosed.
- The Alphabet DCF is highly terminal-sensitive and should not be treated as a
  precise price target.

Analytical research on public information. Not investment advice, a
recommendation, or a solicitation.
