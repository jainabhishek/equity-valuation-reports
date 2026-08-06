"""Clean base year for both names, with the quality-of-earnings adjustments made explicit.

The published reports use reported TTM figures. For Alphabet that means a base
year in which non-operating equity-securities gains exceed operating income.
The DCF itself keys off EBIT and so is insulated -- but every multiple, every
EPS figure, and the equity bridge are not.
"""
import json
from datetime import date
from pathlib import Path

import sec
import series

# Bridge roles map to a LIST of tags that are summed. Companies present the
# same economic item under different tags and at different levels of
# aggregation; a single tag per role silently returns zero (NVDA reports no
# CashCashEquivalentsAndShortTermInvestments at all).

# Preferred is the role most exposed to the silent-zero failure: most filers
# most of the time genuinely have none, so a zero reads as correct. These tags
# are ALTERNATIVE presentations of the same line, not components to add up --
# `build` refuses to proceed if more than one matches. Alphabet's 6.25%
# mandatory convertible, issued June 2026, is tagged with APIC folded in and
# does not report PreferredStockValue at all; carrying a single tag here put
# $18.0bn through the bridge as zero.
PREFERRED_TAGS = [
    "PreferredStockValue",
    "ConvertiblePreferredStockNonredeemableOrRedeemableIssuerOptionValue",
    "PreferredStockIncludingAdditionalPaidInCapitalValue",
]

SPEC = {
    "GOOGL": {
        "cik": "0001652044",
        "as_of": "2026-06-30",
        "shares_tag": "WeightedAverageNumberOfDilutedSharesOutstanding",
        "bridge": {
            # cash + marketable DEBT securities. Ties to the published 242,474.
            "cash_and_marketable": ["CashCashEquivalentsAndShortTermInvestments"],
            # non-operating investment portfolio, excluded from the published bridge
            "equity_investments": ["EquitySecuritiesWithoutReadilyDeterminableFairValueAmount"],
            "debt": ["LongTermDebtNoncurrent", "LongTermDebtCurrent"],
            "leases": ["OperatingLeaseLiabilityNoncurrent", "OperatingLeaseLiabilityCurrent"],
            "preferred": PREFERRED_TAGS,
        },
    },
    "NVDA": {
        "cik": "0001045810",
        "as_of": "2026-04-26",
        "shares_tag": "WeightedAverageNumberOfDilutedSharesOutstanding",
        "bridge": {
            "cash_and_marketable": [
                "CashAndCashEquivalentsAtCarryingValue",
                "AvailableForSaleSecuritiesDebtSecurities",
            ],
            # marketable + non-marketable equity stakes: the vendor-financing question
            "equity_investments": [
                "EquitySecuritiesFvNi",
                "EquitySecuritiesWithoutReadilyDeterminableFairValueAmount",
            ],
            "debt": ["LongTermDebtNoncurrent", "LongTermDebtCurrent"],
            "leases": ["OperatingLeaseLiabilityNoncurrent", "OperatingLeaseLiabilityCurrent"],
            "preferred": PREFERRED_TAGS,
        },
    },
}

# Spot prices, regular-session close of 2026-08-06 (the memos' valuation date).
SPOT = {"GOOGL": 357.94, "NVDA": 218.99}


def check_preferred(ticker, as_of, bs, prov, spec):
    """Corroborate the preferred deduction against the share count.

    A bridge role that resolves to zero because no tag matched is
    indistinguishable, downstream, from one that is genuinely zero. Preferred
    shares outstanding is an independent fact in the same filing, so it can
    settle which case we are in. This is the check that would have caught
    Alphabet's mandatory convertible instead of shipping it as a zero.
    """
    parts = prov["bs.preferred"]
    matched = [p for p in parts if "val" in p]
    if len(matched) > 1:
        raise RuntimeError(
            f"{ticker}: {len(matched)} preferred tags matched ({[p['tag'] for p in matched]}). "
            "These are alternative presentations of one line, so summing double-counts. "
            "Narrow PREFERRED_TAGS for this filer."
        )

    shares = sec.instant(ticker, "PreferredStockSharesOutstanding", unit="shares")
    dates = [x for x in shares if str(x) <= as_of]
    outstanding = shares[max(dates)]["val"] if dates else 0.0
    if outstanding > 0 and bs.get("preferred", 0.0) == 0.0:
        raise RuntimeError(
            f"{ticker}: {outstanding:,.0f} preferred shares outstanding at {max(dates)}, but the "
            f"bridge resolved preferred to 0 -- none of {spec['bridge']['preferred']} matched. "
            "Find the tag this filer uses and add it to PREFERRED_TAGS."
        )
    if outstanding == 0 and bs.get("preferred", 0.0) != 0.0:
        raise RuntimeError(
            f"{ticker}: preferred carrying value {bs['preferred']:,.0f} with no preferred shares "
            f"outstanding at {as_of}. The matched tag is probably not what it appears to be."
        )


def build(ticker):
    spec = SPEC[ticker]
    as_of = spec["as_of"]
    d = series.load(ticker)

    ttm = {}
    prov = {}
    for k, (tag, s) in d.items():
        if not s:
            ttm[k] = None
            continue
        v, w, ok = series.ttm(s, as_of=as_of)
        if not ok or v is None:
            ttm[k] = None
            prov[k] = {"tag": tag, "status": "rejected_window"}
            continue
        ttm[k] = v
        prov[k] = {
            "tag": tag,
            "window": [str(w[0]), str(w[-1])],
            "bases": sorted({s[e]["basis"] for e in w}),
            "accns": sorted({s[e]["accn"] for e in w}),
        }

    # NVDA reports capex under PaymentsToAcquireProductiveAssets
    if ttm.get("capex") is None:
        tag, s = series.first_tag(ticker, ["PaymentsToAcquireProductiveAssets"])
        if s:
            v, w, ok = series.ttm(s, as_of=as_of)
            if ok:
                ttm["capex"] = v
                prov["capex"] = {"tag": tag, "window": [str(w[0]), str(w[-1])], "bases": ["ytd_diff"]}

    bs = {}
    for role, tags in spec["bridge"].items():
        total, parts = 0.0, []
        for tag in tags:
            inst = sec.instant(ticker, tag)
            if not inst:
                continue
            dates = [x for x in inst if str(x) <= as_of]
            if not dates:
                continue
            e = max(dates)
            # A stale balance-sheet item is a real risk (NVDA stopped tagging
            # MarketableSecuritiesCurrent). Refuse anything older than ~2 quarters.
            edate = e if isinstance(e, date) else date.fromisoformat(str(e))
            if (date.fromisoformat(as_of) - edate).days > 200:
                parts.append({"tag": tag, "status": "stale", "date": str(e)})
                continue
            total += inst[e]["val"]
            parts.append({"tag": tag, "val": inst[e]["val"], "date": str(e), "accn": inst[e]["accn"]})
        bs[role] = total
        prov[f"bs.{role}"] = parts

    check_preferred(ticker, as_of, bs, prov, spec)

    sh = sec.quarterly(ticker, spec["shares_tag"], unit="shares")
    e = max(x for x in sh if str(x) <= as_of)
    diluted = sh[e]["val"]

    ebit = ttm["operating_income"]
    tax_rate = ttm["tax"] / ttm["pretax"]
    nopat = ebit * (1 - tax_rate)
    reported_ni = ttm["net_income"]
    gains = ttm.get("equity_sec_gains") or 0.0

    out = {
        "ticker": ticker,
        "as_of": as_of,
        "spot": SPOT[ticker],
        "diluted_shares_m": diluted / 1e6,
        "ttm": {k: (None if v is None else v) for k, v in ttm.items()},
        "balance_sheet": bs,
        "derived": {
            "effective_tax_rate": tax_rate,
            "ebit_margin": ebit / ttm["revenue"],
            "nopat": nopat,
            "reported_net_income": reported_ni,
            "nonoperating_share_of_pretax": ttm["nonoperating"] / ttm["pretax"],
            "equity_sec_gains": gains,
            "reported_eps": reported_ni / diluted,
            "economic_eps": nopat / diluted,
            "reported_pe": SPOT[ticker] / (reported_ni / diluted),
            "economic_pe": SPOT[ticker] / (nopat / diluted),
            "fcf_cfo_less_capex": ttm["cfo"] - ttm["capex"],
            "fcff": nopat + ttm["da"] - ttm["capex"],
            "capex_pct_revenue": ttm["capex"] / ttm["revenue"],
            "da_pct_revenue": ttm["da"] / ttm["revenue"],
            "sbc_pct_revenue": ttm["sbc"] / ttm["revenue"],
            "net_debt": bs["debt"] + bs["leases"] - bs["cash_and_marketable"],
            "equity_investments_per_share": bs["equity_investments"] / diluted,
            "equity_investments_pct_revenue": bs["equity_investments"] / ttm["revenue"],
        },
        "provenance": prov,
    }
    return out


def fmt_row(label, val, unit="$bn", dp=1):
    if val is None:
        return f"{label:<40} {'n/a':>12}"
    if unit == "$bn":
        return f"{label:<40} {val / 1e9:>12,.1f}"
    if unit == "%":
        return f"{label:<40} {val * 100:>11,.1f}%"
    return f"{label:<40} {val:>12,.{dp}f}"


if __name__ == "__main__":
    out = {}
    for t in ("GOOGL", "NVDA"):
        b = build(t)
        out[t] = b
        d, s = b["derived"], b["ttm"]
        print(f"\n{'=' * 56}\n{t}  base year TTM to {b['as_of']}   spot ${b['spot']}\n{'=' * 56}")
        print(fmt_row("Revenue", s["revenue"]))
        print(fmt_row("Operating income (EBIT)", s["operating_income"]))
        print(fmt_row("  EBIT margin", d["ebit_margin"], "%"))
        print(fmt_row("Non-operating income", s["nonoperating"]))
        print(fmt_row("  equity-securities gains", d["equity_sec_gains"]))
        print(fmt_row("  non-op as % of pretax", d["nonoperating_share_of_pretax"], "%"))
        print(fmt_row("Reported net income", d["reported_net_income"]))
        print(fmt_row("NOPAT (EBIT x (1-t))", d["nopat"]))
        print(fmt_row("  effective tax rate", d["effective_tax_rate"], "%"))
        print("-" * 56)
        print(fmt_row("Reported diluted EPS", d["reported_eps"], "x", 2))
        print(fmt_row("Economic EPS (NOPAT-based)", d["economic_eps"], "x", 2))
        print(fmt_row("Reported P/E", d["reported_pe"], "x", 1))
        print(fmt_row("Economic P/E", d["economic_pe"], "x", 1))
        print("-" * 56)
        print(fmt_row("CFO", s["cfo"]))
        print(fmt_row("Capex", s["capex"]))
        print(fmt_row("  capex % revenue", d["capex_pct_revenue"], "%"))
        print(fmt_row("D&A", s["da"]))
        print(fmt_row("FCF (CFO - capex)", d["fcf_cfo_less_capex"]))
        print(fmt_row("FCFF (NOPAT + D&A - capex)", d["fcff"]))
        print(fmt_row("SBC", s["sbc"]))
        print(fmt_row("Buybacks", s["buybacks"]))
        print("-" * 56)
        print(fmt_row("Cash + marketable securities", b["balance_sheet"]["cash_and_marketable"]))
        print(fmt_row("Equity investments (stakes)", b["balance_sheet"]["equity_investments"]))
        print(fmt_row("  per share ($)", d["equity_investments_per_share"], "x", 2))
        print(fmt_row("  as % of revenue", d["equity_investments_pct_revenue"], "%"))
        print(fmt_row("Debt", b["balance_sheet"]["debt"]))
        print(fmt_row("Leases", b["balance_sheet"]["leases"]))
        print(fmt_row("Preferred", b["balance_sheet"]["preferred"]))
        print(fmt_row("Net debt (incl. leases)", d["net_debt"]))
        print(fmt_row("Diluted shares (m)", b["diluted_shares_m"], "x", 0))

    Path("data").mkdir(exist_ok=True)
    Path("data/base_year.json").write_text(json.dumps(out, indent=2, default=str))
    print("\nwrote data/base_year.json")
