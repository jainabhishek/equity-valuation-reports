"""Robust quarterly series construction from SEC XBRL duration facts.

Two traps this exists to handle:
  1. Q4 is never filed as a standalone fact. 10-Ks report the full year, so Q4
     must be derived as FY minus the 9-month YTD.
  2. 10-Q cash-flow statements are cumulative from fiscal-year start, so a
     "~90 day duration" filter only ever catches Q1.

Both produce silently-wrong TTM figures rather than errors, which is why they
get their own module and a self-check.
"""
from datetime import date

import sec


def _facts(ticker, tag, taxonomy="us-gaap", unit=None):
    p = sec.concept(ticker, tag, taxonomy)
    if p is None:
        return []
    rows = []
    for u in sec._rows(p, unit):
        if not u.get("start") or not u.get("end"):
            continue
        rows.append(
            {
                "start": date.fromisoformat(u["start"]),
                "end": date.fromisoformat(u["end"]),
                "days": (date.fromisoformat(u["end"]) - date.fromisoformat(u["start"])).days,
                "val": u["val"],
                "form": u["form"],
                "accn": u["accn"],
                "filed": u["filed"],
            }
        )
    best = {}
    for r in rows:
        k = (r["start"], r["end"])
        if k not in best or r["filed"] >= best[k]["filed"]:
            best[k] = r
    return sorted(best.values(), key=lambda r: (r["start"], r["end"]))


def quarters(ticker, tag, taxonomy="us-gaap", unit=None):
    """{period_end (date): {val, basis, accn}} for single fiscal quarters.

    basis records how the number was obtained: 'filed' (reported directly),
    'ytd_diff' (cumulative unwound), or 'fy_minus_9m' (Q4 derived).
    """
    rows = _facts(ticker, tag, taxonomy, unit)
    if not rows:
        return {}

    out = {}
    # Pass 1 — directly filed single quarters.
    for r in rows:
        if 80 <= r["days"] <= 100:
            out[r["end"]] = {"val": r["val"], "basis": "filed", "accn": r["accn"], "start": r["start"]}

    # Pass 2 — unwind cumulative YTD runs sharing a fiscal-year start.
    by_start = {}
    for r in rows:
        by_start.setdefault(r["start"], []).append(r)
    for start, group in sorted(by_start.items()):
        group = sorted(group, key=lambda r: r["end"])
        prev = None
        for r in group:
            if r["days"] <= 100:
                prev = r
                continue
            if prev is not None and r["end"] not in out:
                out[r["end"]] = {
                    "val": r["val"] - prev["val"],
                    "basis": "ytd_diff",
                    "accn": r["accn"],
                    "start": prev["end"],
                }
            prev = r

    # Pass 3 — derive Q4 as FY minus the longest sub-year cumulative sharing its start.
    for start, group in sorted(by_start.items()):
        annuals = [r for r in group if 350 <= r["days"] <= 380]
        partials = [r for r in group if 150 <= r["days"] <= 300]
        if not annuals or not partials:
            continue
        fy = max(annuals, key=lambda r: r["end"])
        nine = max(partials, key=lambda r: r["days"])
        if fy["end"] in out:
            continue
        out[fy["end"]] = {
            "val": fy["val"] - nine["val"],
            "basis": "fy_minus_9m",
            "accn": fy["accn"],
            "start": nine["end"],
        }
    return dict(sorted(out.items()))


def ttm(series, as_of=None, n=4):
    """Sum trailing n quarters. Returns (value, window, ok).

    ok is False when the window has a gap or overlap — never silently sum a
    broken window, since that is precisely how a wrong base year ships.
    """
    ends = sorted(series)
    if as_of:
        if isinstance(as_of, str):
            as_of = date.fromisoformat(as_of)
        ends = [e for e in ends if e <= as_of]
    if len(ends) < n:
        return None, ends, False
    window = ends[-n:]
    # contiguity: each quarter should start roughly where the previous ended
    ok = True
    for a, b in zip(window, window[1:]):
        gap = (b - a).days
        if not (80 <= gap <= 100):
            ok = False
    return sum(series[e]["val"] for e in window), window, ok


def first_tag(ticker, candidates, taxonomy="us-gaap", unit=None):
    """Return (tag, series) for the first candidate that reports data."""
    for tag in candidates:
        s = quarters(ticker, tag, taxonomy, unit)
        if s:
            return tag, s
    return None, {}


# Tag fallback chains. Companies do not agree on tags; a single global map
# silently yields nulls (Alphabet does not use `Revenues` post-2024).
CHAINS = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "operating_income": ["OperatingIncomeLoss"],
    "gross_profit": ["GrossProfit"],
    "cost_of_revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
    "rnd": ["ResearchAndDevelopmentExpense"],
    "nonoperating": ["NonoperatingIncomeExpense"],
    "equity_sec_gains": [
        "EquitySecuritiesFvNiGainLoss",
        "EquitySecuritiesFvNiUnrealizedGainLoss",
        "MarketableSecuritiesRealizedGainLoss",
    ],
    "pretax": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ],
    "tax": ["IncomeTaxExpenseBenefit"],
    "net_income": ["NetIncomeLoss"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsToAcquirePropertyPlantAndEquipmentAndIntangibleAssets",
    ],
    "da": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet", "Depreciation"],
    "sbc": ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"],
    "buybacks": ["PaymentsForRepurchaseOfCommonStock"],
    "interest_expense": ["InterestExpense", "InterestExpenseNonoperating", "InterestIncomeExpenseNet"],
}


def load(ticker, keys=None):
    """{key: (tag, series)} using the fallback chains."""
    out = {}
    for k, chain in CHAINS.items():
        if keys and k not in keys:
            continue
        out[k] = first_tag(ticker, chain)
    return out
