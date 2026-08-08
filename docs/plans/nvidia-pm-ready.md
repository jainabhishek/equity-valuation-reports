# Nvidia PM-ready remediation plan

## Objective

Rebuild the Nvidia memo and workbook for a hedge-fund PM discussion. The
deliverable must separate a polished research package from a capital-ready
trade. It may recommend zero risk when the evidence, implementation, or variant
is incomplete.

## Highest-priority findings

1. The memo contradicts itself on expected upside and contains an Alphabet WACC
   reference. Remove both defects and make the decision language consistent.
2. Q1 FY2027 equity-security gains are shown as zero even though the filing
   reports $15.936bn. Correct the quality-of-earnings analysis and prevent a
   rejected source tag from silently becoming zero.
3. FY2027 D&A is below a defensible annual run-rate after Q1 actual D&A and the
   disclosed remaining amortization. Replace the incomplete historical-vintage
   schedule with an opening D&A block plus formula-driven forecast vintages.
4. The model uses Nvidia's retired product-market disclosure as though it were
   current. Re-anchor the near-term build on Q1 actual revenue, Q2 guidance and a
   consolidated forecast; retain Data Center and Edge as current reported facts.
5. The WACC is hardcoded but described as CAPM-derived. Add a sourced Treasury
   rate, explicit beta and ERP assumptions, after-tax debt cost and market-value
   weights. Show the market-implied WACC.
6. The terminal value capitalizes unnormalized FCFF. Normalize reinvestment with
   terminal growth divided by terminal ROIC and expose the terminal-value share.
7. The equity bridge gives full credit to strategic and illiquid equity stakes
   and overstates customer-financing evidence. Split liquid cash, public equity,
   private equity and equity-method stakes; apply visible haircuts and state that
   the filing says only some investees may indirectly use Nvidia products.
8. The probability-weighted value has no evidence-grade probability basis.
   Remove it from the decision and sizing logic. Treat scenarios as states, not
   forecasts with false precision.

## Required before risking capital

- Freeze broker-level consensus with provider, retrieval timestamp, statistic,
  cohort and revision history around the next earnings event.
- Freeze the estimate tape before Nvidia's confirmed August 26 Q2 event, then
  reconcile actuals, guidance and post-print revisions to the model.
- Quantify customer-financing and strategic-investment demand exposure instead
  of treating the entire investment portfolio as customer funding.
- Obtain channel, lead-time, backlog and cancellation evidence sufficient to
  distinguish durable demand from pull-forward.
- Refresh price, liquidity, options, short interest, borrow and crowding at the
  decision time.
- Complete the portfolio implementation ledger: current exposure, risk budget,
  beta and factor loadings, hedge, drawdown limit and event-loss limit.
- Require an observable variant and at least 20% underwritten upside or downside
  after implementation costs before assigning non-zero size.

## Implementation

1. Build one Python calculation layer for the source ledger, scenarios, DCF,
   reverse DCF, checks and HTML memo.
2. Build the Excel workbook separately with `@oai/artifact-tool`; every key
   output must be formula-linked to visible assumptions.
3. Add Cover, Decision, Sources, Drivers, Revenue, WACC, Depreciation, Equity
   Bridge, Scenarios, Valuation, Reverse DCF, Sensitivities, Checks and Notes
   sheets in that order.
4. Extend independent verification to compare Python outputs with workbook
   formulas and to fail on the legacy errors above.
5. Render every worksheet and inspect the memo at desktop and mobile widths.
6. Commit generated and source artifacts, push the branch and open a pull
   request.

## Acceptance criteria

- The memo is internally consistent and labels the output `WATCHLIST / NO
  POSITION`, with public evidence sufficient to stay flat and insufficient to
  initiate a position.
- Q1 equity-security gains, current reporting architecture, WACC, terminal
  reinvestment, D&A and the equity bridge are corrected.
- Bear, base and bull values are formula-driven and ordered.
- The workbook contains a first-visible Cover, a second-tab Decision page,
  source ledger, evidence gates and pass/fail checks.
- No formula errors appear in the final workbook; Python and workbook headline
  outputs tie within stated tolerances.
- The memo has no horizontal overflow at mobile width and no unresolved browser
  errors caused by the artifact.
