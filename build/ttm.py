"""Derive true quarterly cash-flow figures from cumulative YTD filings, then TTM.

10-Q cash-flow statements are cumulative from fiscal-year start, so a naive
"duration ~90 days" filter only ever catches Q1. Everything downstream (capex
intensity, FCF, the whole reinvestment argument) is wrong if this is wrong.
"""
from datetime import date

import sec

FY_START = {"GOOGL": (1, 1), "NVDA": (1, 26)}  # approximate fiscal-year start


def _durations(ticker, tag, taxonomy="us-gaap"):
    p = sec.concept(ticker, tag, taxonomy)
    if p is None:
        return []
    rows = []
    for u in sec._rows(p):
        if not u.get("start") or not u.get("end"):
            continue
        rows.append(
            {
                "start": date.fromisoformat(u["start"]),
                "end": date.fromisoformat(u["end"]),
                "val": u["val"],
                "form": u["form"],
                "accn": u["accn"],
                "filed": u["filed"],
            }
        )
    # dedupe on (start,end) keeping latest filing
    best = {}
    for r in rows:
        k = (r["start"], r["end"])
        if k not in best or r["filed"] >= best[k]["filed"]:
            best[k] = r
    return sorted(best.values(), key=lambda r: (r["end"], r["start"]))


def quarterly_from_ytd(ticker, tag, taxonomy="us-gaap"):
    """Return {period_end: value} for single quarters, unwinding YTD cumulatives."""
    rows = _durations(ticker, tag, taxonomy)
    if not rows:
        return {}
    by_start = {}
    for r in rows:
        by_start.setdefault(r["start"], []).append(r)

    out = {}
    for start, group in by_start.items():
        group = sorted(group, key=lambda r: r["end"])
        prev_end, prev_val = None, 0.0
        for r in group:
            days = (r["end"] - r["start"]).days
            if days <= 100:  # already a single quarter
                out.setdefault(r["end"], r["val"])
                prev_end, prev_val = r["end"], r["val"]
            elif prev_end is not None:
                # cumulative: this period minus the prior cumulative from the same start
                out.setdefault(r["end"], r["val"] - prev_val)
                prev_end, prev_val = r["end"], r["val"]
            else:
                prev_end, prev_val = r["end"], r["val"]
    return dict(sorted(out.items()))


def ttm(series: dict, as_of: str | None = None, n: int = 4):
    """Sum the trailing n quarters ending at or before as_of."""
    ends = sorted(series)
    if as_of:
        ends = [e for e in ends if e <= as_of]
    if len(ends) < n:
        return None, ends[-n:] if ends else []
    window = ends[-n:]
    return sum(series[e] for e in window), window


IS_Q = {
    "revenue": "Revenues",
    "operating_income": "OperatingIncomeLoss",
    "nonoperating": "NonoperatingIncomeExpense",
    "equity_sec_gains": "EquitySecuritiesFvNiGainLoss",
    "pretax": "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "tax": "IncomeTaxExpenseBenefit",
    "net_income": "NetIncomeLoss",
}
CF_Q = {
    "cfo": "NetCashProvidedByUsedInOperatingActivities",
    "capex": "PaymentsToAcquirePropertyPlantAndEquipment",
    "sbc": "ShareBasedCompensation",
    "buybacks": "PaymentsForRepurchaseOfCommonStock",
    "depreciation": "Depreciation",
    "da": "DepreciationDepletionAndAmortization",
}


def build(ticker, as_of=None):
    out = {}
    for k, tag in IS_Q.items():
        out[k] = sec.quarterly(ticker, tag)
        out[k] = {e: v["val"] for e, v in out[k].items()}
    for k, tag in CF_Q.items():
        out[k] = quarterly_from_ytd(ticker, tag)
    return out


def report(ticker, as_of=None):
    q = build(ticker, as_of)
    print(f"\n{'=' * 78}\n{ticker} — trailing-twelve-month, $bn\n{'=' * 78}")
    rows = [
        ("Revenue", "revenue"),
        ("Operating income", "operating_income"),
        ("Non-operating income", "nonoperating"),
        ("  equity-securities gains", "equity_sec_gains"),
        ("Pretax income", "pretax"),
        ("Tax expense", "tax"),
        ("Net income (reported)", "net_income"),
        ("Cash from operations", "cfo"),
        ("Capex", "capex"),
        ("Depreciation", "depreciation"),
        ("D&A", "da"),
        ("Stock-based comp", "sbc"),
        ("Buybacks", "buybacks"),
    ]
    vals = {}
    for label, k in rows:
        v, window = ttm(q[k], as_of)
        vals[k] = v
        w = f"{window[0]}..{window[-1]}" if window else "-"
        print(f"{label:<28} {('n/a' if v is None else f'{v / 1e9:>10,.1f}')}   [{w}]")
    return q, vals
