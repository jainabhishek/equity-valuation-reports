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

# Financing that happened AFTER the balance-sheet date but before the valuation
# date. The bridge is otherwise a snapshot of a filing, and a filing goes stale:
# Alphabet priced $25.0bn of senior unsecured notes on 6 August 2026, five weeks
# after the 30 June balance sheet the bridge is built from. A reader pricing the
# equity on 7 August is pricing a company that owes that money.
#
# Both legs are carried, so the net effect is only the underwriting spread --
# about $0.2bn, two cents a share. That is the point: the number is small, and
# the way to know it is small is to put it through rather than to assume it.
# Nothing here is a forecast; each entry is a priced, publicly documented
# transaction with an SEC accession number.
POST_BALANCE_SHEET = {
    "GOOGL": [{
        "event": "$25.0bn senior unsecured notes, 10 tranches, 2028-2066 maturities",
        "priced": "2026-08-06",
        "settles": "2026-08-10",
        "accn": "0001193125-26-340264",
        "form": "424B2",
        "debt": 25_000_000_000.0,
        "cash_and_marketable": 24_800_000_000.0,   # stated net proceeds
        "note": ("Priced but not yet settled at the valuation date. Carried at both legs: the "
                 "obligation is binding and the proceeds are contracted, so omitting either "
                 "would misstate the bridge by $25bn in one direction or the other."),
    }],
}

# Authorised but undrawn. NOT applied: nothing has been issued, and putting
# unissued shares into a share count is inventing a fact. Recorded here because
# a $40bn equity programme sitting over a per-share valuation is something the
# memo has to say out loud, and because the day it starts drawing this file is
# where the adjustment goes.
AUTHORISED_UNDRAWN = {
    "GOOGL": [{
        "event": "At-the-market programme, up to $40.0bn of Class A and Class C stock",
        "established": "2026-06-01",
        "amended": "2026-08-06",
        "drawn_as_of": "2026-06-30",
        "drawn": 0.0,
        "capacity": 40_000_000_000.0,
        "source": ("Q2 2026 Form 8-K Exhibit 99.1: \"As of June 30, 2026, we have not sold any "
                   "shares under the ATM Program.\" Managers expanded 2026-08-06 (424B5 "
                   "0001193125-26-336853)."),
        "purpose": "proceeds primarily intended to meet tax obligations on employee equity grants",
    }],
}

# Spot prices, last regular-session trade of 2026-08-07 (the memos' valuation
# date), 16:00 ET. The consolidated settled close for that session had not been
# published when this was built, so these are the last regular-hours prints
# rather than official closes; both are within a cent of the closing auction on
# the prior session and the distinction does not move any figure in the memo.
SPOT = {"GOOGL": 354.24, "NVDA": 223.90}


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


def build_ytd(ticker, as_of, loaded):
    """Fiscal-year-to-date actuals, plus the last observed quarter as an exit rate.

    Forecast year 1 is part history: at 2026-06-30 Alphabet's calendar 2026 is
    half reported. Modelling the whole year from a trailing-twelve-month ratio
    throws that half away, and is how a full-year capex forecast ended up below
    six months of actual spend. The forecast anchors on these figures instead.
    """
    out = {}
    for k in ("capex", "revenue", "cfo"):
        y = series.fiscal_ytd(ticker, series.CHAINS[k], as_of)
        if y is None:
            raise RuntimeError(f"{ticker}: no fiscal-YTD {k} fact ending {as_of}")
        # Cross-check the filed cumulative against our own unwound quarters. A
        # mismatch means the quarter derivation is wrong, which would otherwise
        # corrupt the TTM base year silently.
        q = loaded[k][1]
        elapsed = sorted(e for e in q if str(e) <= as_of)[-y["quarters_elapsed"]:]
        derived = sum(q[e]["val"] for e in elapsed)
        if y["val"] and abs(derived - y["val"]) / abs(y["val"]) > 0.005:
            raise RuntimeError(
                f"{ticker}: filed YTD {k} {y['val']:,.0f} disagrees with the sum of our "
                f"{len(elapsed)} unwound quarters {derived:,.0f}. The quarter derivation is wrong."
            )
        out[k] = y

    q = loaded["capex"][1]
    exit_end = max(e for e in q if str(e) <= as_of)
    out["exit_quarter_capex"] = {"val": q[exit_end]["val"], "period_end": str(exit_end),
                                 "basis": q[exit_end]["basis"]}
    out["quarters_elapsed"] = out["capex"]["quarters_elapsed"]
    out["quarters_remaining"] = 4 - out["quarters_elapsed"]
    return out


def build(ticker):
    spec = SPEC[ticker]
    as_of = spec["as_of"]
    d = series.load(ticker, as_of=as_of)

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

    # Every TTM line is load-bearing; none may silently resolve to nothing.
    for k in ("revenue", "operating_income", "capex", "da", "cfo", "net_income"):
        if ttm.get(k) is None:
            raise RuntimeError(
                f"{ticker}: no usable TTM {k} at {as_of} from {series.CHAINS[k]}. "
                f"Provenance: {prov.get(k)}"
            )

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

    # Roll the filed balance sheet forward for financing done between the
    # balance-sheet date and the valuation date. Kept as a separate, itemised
    # layer so the memo can show the filed figure and the adjustment side by
    # side rather than presenting a derived number as a filed one.
    bs_filed = dict(bs)
    post = POST_BALANCE_SHEET.get(ticker, [])
    for item in post:
        for role in ("cash_and_marketable", "equity_investments", "debt", "leases", "preferred"):
            if role in item:
                if role not in bs:
                    raise RuntimeError(
                        f"{ticker}: post-balance-sheet adjustment '{item['event']}' targets bridge "
                        f"role '{role}', which this filer's bridge does not carry."
                    )
                bs[role] += item[role]
    ytd = build_ytd(ticker, as_of, d)

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
        "ytd": ytd,
        "balance_sheet": bs,
        "balance_sheet_as_filed": bs_filed,
        "post_balance_sheet": post,
        "authorised_undrawn": AUTHORISED_UNDRAWN.get(ticker, []),
        "derived": {
            "effective_tax_rate": tax_rate,
            "ebit_margin": ebit / ttm["revenue"],
            "nopat": nopat,
            "reported_net_income": reported_ni,
            "nonoperating_share_of_pretax": ttm["nonoperating"] / ttm["pretax"],
            "equity_sec_gains": gains,
            "reported_eps": reported_ni / diluted,
            "reported_pe": SPOT[ticker] / (reported_ni / diluted),
            "ev_to_nopat": (
                SPOT[ticker] * diluted + bs["debt"] + bs["leases"]
                + bs.get("preferred", 0.0) - bs["cash_and_marketable"]
                - bs["equity_investments"]
            ) / nopat,
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
        print(fmt_row("Reported P/E", d["reported_pe"], "x", 1))
        print(fmt_row("EV / NOPAT", d["ev_to_nopat"], "x", 1))
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
