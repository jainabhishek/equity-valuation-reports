# Equity Valuation Reports

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Live site](https://img.shields.io/badge/live%20site-github.io-0a8f86)](https://jainabhishek.github.io/equity-valuation-reports/)
[![As of](https://img.shields.io/badge/as%20of-Aug%207%2C%202026-172033)](#)
[![Model](https://img.shields.io/badge/model-segment%20driver%20%2B%20FCFF%20DCF-2864dc)](#)

Buy-side investment memos on individual companies. Each is a self-contained HTML
memo — rating, variant versus consensus, expected value, sizing, kill criteria —
backed by a live Excel model whose every driver is an input cell.

The distinguishing choice: **no forecast line is a bare growth rate.** Revenue is
the product of named quantities (Search = queries × ad coverage × price-per-click),
and EBIT is *derived* by subtracting a vintage depreciation schedule rather than
assumed as a margin. That makes each number something a reader can disagree with
individually, and checkable against the next filing.

**Live site:** [jainabhishek.github.io/equity-valuation-reports](https://jainabhishek.github.io/equity-valuation-reports/)

## Memos

| | Alphabet (GOOGL) | Nvidia (NVDA) |
| --- | --- | --- |
| **Rating** | **SHORT** · conviction 2/3 · 18-month horizon | **NO POSITION** · conviction 1/3 |
| Spot | $354.24 | $223.90 |
| Bear / base / bull | $107.50 / $190.51 / $442.53 | $67.39 / $197.39 / $437.47 |
| Expected value | **$245.37 (−30.7%)** | **$224.91 (+0.5%)** |
| Risk / reward | 1.23 : 1 | 0.01 : 1 |
| Breakeven p(bull) | 69% | 25% |
| Position size | 5.00% of NAV *(concentration cap binding)* | 0.00% |
| Street-calibrated value | $160.36 | $231.98 |
| Street price target | $427.55 | $319.48 |
| Memo | [Open →](https://jainabhishek.github.io/equity-valuation-reports/alphabet/memo.html) | [Open →](https://jainabhishek.github.io/equity-valuation-reports/nvidia/memo.html) |
| Model | [Download](alphabet/model.xlsx) | [Download](nvidia/model.xlsx) |

Base year: trailing twelve months to 2026-06-30 (GOOGL) and 2026-04-26 (NVDA).
Market data as of the 2026-08-07 session. Earlier editions are kept at their own
dated URLs — see [the archive](archive/index.html).

### Alphabet — the variant is depreciation, stated in EPS

Put our depreciation schedule through the Street's own revenue and EBITDA and
**2027 EPS is $12.20 against the $15.01 that forty-two analysts publish** — a
19% gap that a printed number tests every ninety days. That is the variant.

It is deliberately *not* stated as "consensus carries D&A at 4.6% of revenue",
which is how earlier editions put it. That comparison was weaker than it looked:
the feed's EBIT margin is **32.48%** and its implied D&A **4.62%** in every
single forecast year, to four significant figures, with EBIT growth equal to
revenue growth to a decimal place in all of them. That is a vendor holding a
ratio constant against a revenue consensus, not forty analysts agreeing on a
margin. Published EPS is a real forecast with a real cohort behind it, so that
is what the variant is now measured against.

The underlying arithmetic is unchanged. Forecast year 2026 is anchored on
management guidance: **$80.6bn** of first-half capex is reported fact, and on
22 July the CFO guided the full year to **$195–205bn**, up from $180–190bn. The
base case takes the $200bn midpoint — **$59.7bn** in each remaining quarter
against the $44.9bn just reported. Over 2026–31 that path spends **$1,093bn**
while the consensus feed depreciates only **$193bn** of it, a **$381bn** gap,
and by 2031 **$95bn** a year of charge the consensus EBIT margin never takes.

Management has also said the charge is coming, in terms: capex will "increase
significantly in 2027", bringing "higher depreciation expense and related data
center operations costs such as energy". The spending leg of the thesis is no
longer a forecast we have to defend, and it is checkable every ninety days from
the filings — which is what makes it a position rather than an opinion.

**The discount rate is worth more than the depreciation argument, and the memo
now says so.** Terminal value is 89% of enterprise value and the base case
discounts at 8.75%. Published third-party estimates of Alphabet's WACC cluster
near **7.57%**, which on this same model gives **$243.01** rather than $190.51;
the reverse DCF implies the market is discounting at **6.19%**. A reader who
prefers 7.5% and accepts every other number here is most of the way to the
Street's range without disagreeing with the thesis at all. The full sensitivity
is published in the memo rather than left implicit in one input.

A quality-of-earnings pass also matters here: Alphabet's trailing twelve months
include **$149bn of equity-securities gains — 50.7% of pretax income**. Reported
P/E of **17.9×** is **36.2×** on operating earnings.

Alphabet is funding the build in the capital markets, and the memo carries each
piece explicitly: **$49.6bn** of net equity proceeds in June (including a $10bn
Berkshire Hathaway private placement) plus a **$25.0bn** ten-tranche note
offering priced 6 August, which the equity bridge picks up as a post-balance-sheet
adjustment. A **$40bn** at-the-market equity programme is authorised and, as of
30 June, entirely undrawn — so it is disclosed rather than put into the share
count.

### Nvidia — no variant, so no position

Our revenue path sits inside the analyst range in every covered year and expected
value is +0.5%, inside the noise. The scenario range spans $67 to $437; no
defensible position size survives that spread. The memo says so rather than
manufacturing a view.

Nearly half of fiscal 2027 is already settled: **$81.6bn** reported for Q1 and
**$91.0bn ±2%** guided for Q2 — **45.3%** of the year fixed before the segment
build says anything. Our full-year figure leaves $104.1bn a quarter for the
remaining two, 14.4% above the guided quarter. Q2 results land **26 August 2026**.

Worth watching regardless: equity stakes in customers now stand at **28.6% of
revenue**, up from roughly 3% a year ago.

## What each folder contains

| File | Description |
| --- | --- |
| `memo.html` | Primary deliverable. Front page: rating, thesis, variant table, Shapley price-to-value bridge, reverse-DCF triple, scenarios and expected value, sizing cascade, kill criteria, catalyst path, falsification and pre-mortem. Appendix: quality of earnings, segment build, equity bridge, sources and limitations. |
| `model.xlsx` | Live model. Every driver is a blue input cell; change ad coverage or ASP and the value per share moves. One WACC definition, referenced everywhere. |
| `archive/` | Every earlier edition at its own dated URL, each with a superseded banner and a note on what changed. Editions are archived, never overwritten: a call is only worth reading against what was knowable when it was made. |

## Method

**Segment driver build.** Each segment compounds by the product of its named
drivers. Alphabet: Search (queries × ad coverage × price-per-click), YouTube
(watch hours × ad load × CPM), Cloud (deliverable capacity), Network (runoff).
Nvidia: Data Center (units × ASP × networking attach) plus the smaller segments.

**Guidance outranks extrapolation.** Where management has guided a period, the
model anchors on the guidance and the build fails if the base case drifts outside
the range; scenarios may disagree with guidance, the base case may not. Where they
have not (Nvidia does not guide capex), reported fiscal-year-to-date spend plus
the exit quarter stands. This exists because an earlier edition extrapolated a
2026 Alphabet capex figure $25bn below a range management had already published:
the build had a floor at capex already reported, but nothing that looked at what
had been guided.

**Every segment is checked against its own reported quarters.** A consolidated
total can be right while the mix inside it is wrong, and consolidated checks
cannot see that. The edition before this one forecast 2026 Cloud revenue of
$91.0bn against $44.8bn already reported — implying $23.1bn in each remaining
quarter, *below* the $24.8bn the June quarter had just printed, in the one
segment growing 82% year over year with a backlog that had added $54bn in three
months to reach $514bn. Consolidated revenue looked entirely reasonable because
other segments were forecast above their own exit rates and absorbed it. Each
segment's implied stub is now measured against its exit quarter, a decline
beyond 2% fails the build unless the reason is written down, and Cloud carries
$97.5bn. Segment revenue is not in XBRL, so the reported quarters are keyed from
the 8-K earnings releases and their sum must tie to the XBRL consolidated
year-to-date figure or the build fails.

**Depreciation is derived, not assumed.** We forecast EBITDA margin — a cash
margin driven by mix, pricing and opex — and subtract a straight-line schedule
over every capex vintage, split between short-lived equipment and long-lived
shells with a half-year convention. Forecasting EBIT margin directly hides the
depreciation assumption inside a single number.

**Valuation.** Six-year unlevered FCFF DCF, mid-year convention, Gordon-growth
terminal value. Enterprise value bridges to equity using cash and marketable
securities, **the non-operating equity investment portfolio**, debt, leases,
preferred stock and diluted shares. Preferred is corroborated against preferred
shares outstanding, so a tag the extractor does not carry fails the build instead
of passing through as zero. A terminal steady-state check compares the reinvestment rate to
the rate implied by g ÷ ROIC, so the model cannot capitalise a terminal cash flow
computed at peak underinvestment.

**Variant versus consensus.** The Street's revenue, EBIT and EBITDA run through
the *identical* engine, so `value(Street) − value(ours)` is pure forecast
disagreement. D&A is the Street's own — EBITDA less EBIT — not ours: their EBIT
margin already embeds their depreciation, so adding back ours would hand them a
cash add-back their own earnings never charged. Capex and working capital are not
supplied by the feed, so those are carried from our case and disclosed.
Attribution uses exact Shapley values over all 2⁷ = 128 driver coalitions, which
sum to the total without residual. The perturbed drivers are EBITDA margin and
D&A, never EBIT directly, because EBIT is *derived* from those two — moving them
independently would double-count depreciation.

**Reverse DCF** is three independent solves — revenue CAGR, terminal EBIT margin,
discount rate — reported as one sentence each. At $354.24 the market is paying for
*either* a 28.0% revenue CAGR, *or* a 46.4% terminal EBIT margin, *or* a 6.19%
discount rate.

**The discount rate is published as a table, not a number.** Terminal value is
89% of enterprise value, so the WACC is not one assumption among many — it is
most of the answer. The memo prints value per share across 6.50%–9.50% with the
base case, the published third-party consensus and the market-implied rate all
marked, because a valuation this far below the market owes the reader the input
that moves it most.

**The bridge is rolled forward, not frozen at the filing.** Financing priced
between the balance-sheet date and the valuation date is itemised with its
accession number and carried on both legs, so a $25bn note issue shows up as the
underwriting spread it actually costs rather than as a $25bn hole or a silent
omission. Authorised-but-undrawn programmes are disclosed and deliberately kept
out of the share count.

**Decision layer.** Probabilities are integers in basis points summing to 10000,
each with a stated anchor. Position size is computed through a constraint cascade
(quarter-Kelly → liquidity → risk budget → concentration cap) with the binding
constraint published. Kill criteria name an observable, a threshold and a date.

## Data

| Need | Source |
| --- | --- |
| Statement historicals, equity bridge, share counts | SEC XBRL `companyconcept` |
| Consensus estimates and price targets | FMP `analyst/*` |
| Segment revenue, annual history | FMP `statements/revenue-product-segmentation` |
| Segment revenue, reported quarters of the forecast year | SEC 8-K earnings releases, by accession number, keyed into `build/cases.py` and reconciled to the XBRL consolidated total |
| Earnings dates and surprise history | Robinhood `get_earnings_results` |
| Prices and average dollar volume | Robinhood `get_equity_quotes`, `get_equity_historicals` |
| Management guidance | The earnings call it was given on, quoted with date and speaker in `build/cases.py` |
| Financing after the balance-sheet date | SEC prospectus filings (424B2/424B5/FWP), by accession number |

Quarterly series are reconstructed from filed facts rather than taken from an
aggregator. Two traps are handled explicitly, because both produce silently wrong
figures rather than errors: **Q4 is never filed standalone** (10-Ks report the
full year, so Q4 is derived as fiscal year minus the nine-month cumulative), and
**10-Q cash-flow statements are cumulative** from fiscal-year start (so a
"~90-day duration" filter only ever catches Q1).

Not used: third-party model outputs — vendor DCFs, quantitative scores, aggregated
ratings. Those are other people's conclusions, not evidence.

## Verification

`model.xlsx` is a second implementation, not a printout of the Python results.
[`build/verify.py`](build/verify.py) recalculates the workbook with a formula
engine and ties it to the Python model — value per share, enterprise value,
equity value, terminal-value share, and FCFF in every forecast year. All 20
checks tie.

```bash
cd build
python3 run.py && python3 render.py    # model -> memos
./.venv/bin/python workbook.py         # -> model.xlsx
./.venv/bin/python previews.py         # -> assets/*.png
./.venv/bin/python verify.py           # workbook vs python
```

Preview and social images are generated from `results.json` rather than hand-made,
so the landing page and social cards cannot drift away from the memos — which is
exactly what had happened to the previous set.

## Known limitations

- **No channel checks, expert calls, or alternative data.** The edge claimed is
  analytical, derived entirely from public filings. Where the honest answer is
  that we have no edge, the memo says so and takes no position.
- **The asset-life split driving the depreciation schedule is a stated assumption**
  calibrated to reported D&A, not a disclosed figure. It is the single most
  load-bearing input in the model, and Alphabet kill criterion k1 exists to
  monitor exactly it.
- **The consensus feed's margin decomposition is a vendor derivation, not an
  analyst forecast.** EBIT margin is 32.48% and implied D&A 4.62% in every single
  forecast year, to four significant figures. Nothing is inferred from it any
  more: the variant is stated against published EPS, which moves independently
  year to year and carries the largest cohort in the feed (42 estimates for
  2027). Independent reporting of Street 2027 EPS ($14.20–$14.68) brackets the
  $15.01 the feed carries, which is the basis for treating that field as real.
- **Whether individual analysts have modelled the depreciation wave is not
  something this data can settle.** Some sell-side commentary says they have. The
  feed cannot confirm it either way, so the memo claims only that our schedule
  implies lower EPS than the published number — not that nobody has thought
  about it.
- **The discount rate moves the answer more than the thesis does.** 8.75% is a
  CAPM build; at the 7.57% third-party estimates cluster around, the base case is
  $243.01 rather than $190.51. The sensitivity is published in full.
- Segment sums reconcile to consolidated revenue within 0.2% (GOOGL) and 1.0% (NVDA).
- Our Alphabet valuation sits well below the Street's median target and below the
  lowest of 39 published targets. That is stated on the front page of the memo,
  along with what would make us wrong.
- **Management guidance is quoted from earnings-call coverage, not from a filing.**
  Alphabet's capex guidance was given on the July 22 call and does not appear in
  the 8-K, the 10-Q, or the August prospectus supplements. It is corroborated
  across independent reports of the call and recorded with its date and speaker,
  but it is the one load-bearing input here that is not a filed fact.
- The August 7 prices are the last regular-session trades rather than official
  settled closes, which had not published when this was built.

## Disclaimer

Analytical research on public information, shared for informational and
educational purposes only. Not investment advice, not a recommendation to any
person, and not a solicitation to buy or sell any security. Position sizing is
illustrative against a notional $1bn book and is not a suggestion that anyone
take a position. Forecasts and assumptions are the author's independent estimates
and may be wrong. Do your own research and consult a licensed financial advisor
before making investment decisions.

## License

Code is licensed under [MIT](LICENSE). Memo content (analysis, narrative,
figures, models) is provided as-is for informational use — see the Disclaimer.
