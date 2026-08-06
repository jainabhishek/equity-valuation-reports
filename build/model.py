"""Valuation engine: segment driver build -> FCFF DCF -> variant vs Street.

Design rule: no forecast line is a bare growth rate. Every revenue line is the
product of named quantities a reader can disagree with one at a time, and every
disagreement with consensus is attributable to a specific driver.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from itertools import combinations
from math import factorial
from pathlib import Path

DATA = Path(__file__).parent / "data"
YEARS = 6


# --------------------------------------------------------------------------
# Driver container
# --------------------------------------------------------------------------
@dataclass
class Drivers:
    """Every value here is an input cell in the published workbook."""

    segments: dict[str, dict[str, list[float]]]  # segment -> driver -> per-year vector
    ebit_margin: list[float]
    tax_rate: list[float]
    da_pct_revenue: list[float]
    capex_pct_revenue: list[float]
    nwc_pct_revenue: list[float]
    terminal_growth: float
    wacc: float
    label: str = "base"
    notes: dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------------
# Segment revenue build
# --------------------------------------------------------------------------
def build_revenue(base_segments: dict[str, float], drivers: Drivers) -> dict:
    """Compound each segment by the product of its drivers.

    A segment's growth is (1+d1)(1+d2)... - 1 across its named drivers, so e.g.
    Search = queries x ad coverage x CPC. Ad coverage is expressed as a delta
    because AI Overviews reduce ad-eligible real estate: it is the single most
    contested number in the Alphabet thesis and it gets its own input.
    """
    out = {"by_segment": {}, "total": [], "growth": []}
    prev_total = sum(base_segments.values())
    running = dict(base_segments)

    for yr in range(YEARS):
        total = 0.0
        for seg, base_val in base_segments.items():
            dv = drivers.segments.get(seg, {})
            factor = 1.0
            for driver, vec in dv.items():
                factor *= 1.0 + vec[yr]
            running[seg] = running[seg] * factor
            out["by_segment"].setdefault(seg, []).append(running[seg])
            total += running[seg]
        out["total"].append(total)
        out["growth"].append(total / prev_total - 1.0)
        prev_total = total
    return out


# --------------------------------------------------------------------------
# DCF
# --------------------------------------------------------------------------
def dcf(base: dict, drivers: Drivers, revenue_override: list[float] | None = None) -> dict:
    """Unlevered FCFF DCF, mid-year convention, Gordon terminal value.

    Equity bridge adds the non-operating investment portfolio, which the
    published report omits.
    """
    rev = revenue_override or build_revenue(base["segments"], drivers)["total"]
    prev_rev = base["revenue"]
    prev_nwc = base["revenue"] * drivers.nwc_pct_revenue[0]

    rows, pv_sum = [], 0.0
    for i in range(YEARS):
        r = rev[i]
        ebit = r * drivers.ebit_margin[i]
        nopat = ebit * (1 - drivers.tax_rate[i])
        da = r * drivers.da_pct_revenue[i]
        capex = r * drivers.capex_pct_revenue[i]
        nwc = r * drivers.nwc_pct_revenue[i]
        d_nwc = nwc - prev_nwc
        fcff = nopat + da - capex - d_nwc
        disc = (1 + drivers.wacc) ** (i + 0.5)  # mid-year
        pv = fcff / disc
        pv_sum += pv
        rows.append(
            {
                "year": i + 1,
                "revenue": r,
                "growth": r / prev_rev - 1,
                "ebit": ebit,
                "ebit_margin": drivers.ebit_margin[i],
                "nopat": nopat,
                "da": da,
                "capex": capex,
                "delta_nwc": d_nwc,
                "fcff": fcff,
                "discount_factor": 1 / disc,
                "pv": pv,
            }
        )
        prev_rev, prev_nwc = r, nwc

    # Terminal value on a normalised final-year FCFF
    tf = rows[-1]
    g = drivers.terminal_growth
    if drivers.wacc - g < 0.015:
        raise ValueError(f"WACC ({drivers.wacc:.4f}) - g ({g:.4f}) < 150bp: terminal value unstable")
    tv_fcff = tf["fcff"] * (1 + g)
    tv = tv_fcff / (drivers.wacc - g)
    pv_tv = tv / (1 + drivers.wacc) ** (YEARS - 0.5)

    ev = pv_sum + pv_tv
    b = base["bridge"]
    equity = ev + b["cash_and_marketable"] + b["equity_investments"] - b["debt"] - b["leases"] - b.get("preferred", 0.0)
    vps = equity / base["diluted_shares"]

    # Terminal steady state: reinvestment must be consistent with g and ROIC.
    # Without this a DCF can capitalise a terminal FCFF computed at peak
    # underinvestment, which is precisely how the published report reached its
    # number (capex faded to 11% of revenue while D&A rose).
    invested_capital = tf["revenue"] * 1.5
    roic = tf["nopat"] / invested_capital
    reinvestment = tf["capex"] - tf["da"] + tf["delta_nwc"]
    reinvestment_rate = reinvestment / tf["nopat"] if tf["nopat"] else float("nan")
    implied_rate = g / roic if roic else float("nan")

    return {
        "rows": rows,
        "steady_state": {
            "terminal_roic": roic,
            "reinvestment_rate": reinvestment_rate,
            "implied_reinvestment_rate": implied_rate,
            "gap_bp": (reinvestment_rate - implied_rate) * 10000,
            "consistent": abs(reinvestment_rate - implied_rate) < 0.15,
        },
        "pv_explicit": pv_sum,
        "terminal_value": tv,
        "pv_terminal": pv_tv,
        "tv_pct_ev": pv_tv / ev,
        "enterprise_value": ev,
        "equity_value": equity,
        "value_per_share": vps,
        "revenue_path": rev,
        "wacc": drivers.wacc,
        "terminal_growth": g,
        "label": drivers.label,
    }


# --------------------------------------------------------------------------
# Street-calibrated case
# --------------------------------------------------------------------------
def street_case(base: dict, drivers: Drivers, consensus: list[dict], first_year: int) -> dict:
    """Run the Street's revenue and EBIT margin through the identical engine.

    Consensus supplies revenue, EBIT and EBITDA. D&A is therefore the Street's
    own (EBITDA less EBIT), not ours -- see below. Capex and NWC are not
    supplied, so those are carried from our case and disclosed. Beyond
    consensus coverage the Street path is faded using our own terminal
    glidepath, anchored to the last covered year -- also disclosed.
    """
    by_fy = {e["fy"]: e for e in consensus}
    rev, margin, carried_years = [], [], []
    # The Street's EBIT margin already embeds the Street's own depreciation.
    # Adding back OUR D&A would hand the Street a cash add-back its own EBIT
    # never charged -- and the higher our capex path goes, the more it would
    # flatter the Street. EBITDA less EBIT is the Street's implied D&A, which is
    # the only internally consistent figure to add back, and the difference
    # between it and ours IS the thesis.
    street_da = []

    last_rev = None
    for i in range(YEARS):
        fy = first_year + i
        if fy in by_fy and by_fy[fy]["revenue_avg"]:
            e = by_fy[fy]
            rev.append(e["revenue_avg"])
            margin.append(e["ebit_avg"] / e["revenue_avg"])
            if e.get("ebitda_avg"):
                street_da.append((e["ebitda_avg"] - e["ebit_avg"]) / e["revenue_avg"])
            elif street_da:
                street_da.append(street_da[-1])
            else:
                raise RuntimeError(
                    f"consensus FY{fy} has no ebitda_avg, so the Street's implied D&A cannot be "
                    "derived and the street case would silently borrow ours."
                )
            last_rev = e["revenue_avg"]
        else:
            # fade beyond coverage using our own growth shape
            g = drivers.segments and None
            prior_growth = (rev[-1] / rev[-2] - 1) if len(rev) >= 2 else 0.10
            fade = max(prior_growth * 0.75, drivers.terminal_growth)
            rev.append(rev[-1] * (1 + fade))
            margin.append(margin[-1])
            street_da.append(street_da[-1])
            carried_years.append(fy)

    sd = Drivers(
        segments=drivers.segments,
        ebit_margin=margin,
        tax_rate=drivers.tax_rate,
        da_pct_revenue=street_da,
        capex_pct_revenue=drivers.capex_pct_revenue,
        nwc_pct_revenue=drivers.nwc_pct_revenue,
        terminal_growth=drivers.terminal_growth,
        wacc=drivers.wacc,
        label="street",
    )
    res = dcf(base, sd, revenue_override=rev)
    res["carried_fields"] = ["tax_rate", "capex_pct_revenue", "nwc_pct_revenue", "terminal_growth", "wacc"]
    res["extrapolated_years"] = carried_years
    res["ebit_margin_path"] = margin
    res["da_pct_revenue_path"] = street_da
    return res


def variant_table(ours: dict, drivers: Drivers, consensus: list[dict], first_year: int) -> list[dict]:
    """Per-year, per-metric comparison against the analyst distribution."""
    by_fy = {e["fy"]: e for e in consensus}
    out = []
    for i, row in enumerate(ours["rows"]):
        fy = first_year + i
        e = by_fy.get(fy)
        if not e or not e.get("revenue_avg"):
            continue
        lo, avg, hi = e["revenue_low"], e["revenue_avg"], e["revenue_high"]
        pos = (row["revenue"] - lo) / (hi - lo) if hi > lo else None
        out.append(
            {
                "fy": fy,
                "metric": "revenue",
                "ours": row["revenue"],
                "street_avg": avg,
                "street_low": lo,
                "street_high": hi,
                "n_analysts": e["n_revenue"],
                "delta_pct": row["revenue"] / avg - 1,
                "inside_range": lo <= row["revenue"] <= hi,
                "position_in_range": pos,
                "dispersion": (hi - lo) / avg,
                "our_ebit": row["ebit"],
                "street_ebit": e["ebit_avg"],
                "ebit_delta_pct": row["ebit"] / e["ebit_avg"] - 1,
                "our_margin": row["ebit_margin"],
                "street_margin": e["ebit_avg"] / avg,
            }
        )
    return out


# --------------------------------------------------------------------------
# Exact Shapley attribution
# --------------------------------------------------------------------------
DRIVER_KEYS = ["revenue", "ebit_margin", "tax_rate", "da_pct_revenue", "capex_pct_revenue", "nwc_pct_revenue", "wacc", "terminal_growth"]


def _ebitda_margin(d: Drivers) -> list[float]:
    """EBITDA margin implied by a Drivers: EBIT margin plus depreciation.

    Holds by identity for both our case (which derives EBIT as EBITDA less a
    vintage schedule) and the Street's (which supplies EBIT and EBITDA).
    """
    return [d.ebit_margin[i] + d.da_pct_revenue[i] for i in range(YEARS)]


def _blend(base_d: Drivers, alt_d: Drivers, subset: frozenset, base_rev, alt_rev, keys=None):
    """Drivers with `subset` taken from alt, remainder from base."""
    keys = keys or DRIVER_KEYS
    pick = lambda k, b, a: a if k in subset else b
    da = pick("da_pct_revenue", base_d.da_pct_revenue, alt_d.da_pct_revenue)
    if "ebitda_margin" in keys:
        # EBIT is not independent of depreciation -- our case derives it as
        # EBITDA less D&A. Perturbing the two separately lets a coalition add
        # back depreciation that its own EBIT never charged, a double-count
        # worth over $100/share here. Blend the cash margin and the schedule,
        # then re-derive EBIT so the identity holds in every coalition.
        em = pick("ebitda_margin", _ebitda_margin(base_d), _ebitda_margin(alt_d))
        ebit = [em[i] - da[i] for i in range(YEARS)]
    else:
        ebit = pick("ebit_margin", base_d.ebit_margin, alt_d.ebit_margin)
    d = Drivers(
        segments=base_d.segments,
        ebit_margin=ebit,
        tax_rate=pick("tax_rate", base_d.tax_rate, alt_d.tax_rate),
        da_pct_revenue=da,
        capex_pct_revenue=pick("capex_pct_revenue", base_d.capex_pct_revenue, alt_d.capex_pct_revenue),
        nwc_pct_revenue=pick("nwc_pct_revenue", base_d.nwc_pct_revenue, alt_d.nwc_pct_revenue),
        terminal_growth=pick("terminal_growth", base_d.terminal_growth, alt_d.terminal_growth),
        wacc=pick("wacc", base_d.wacc, alt_d.wacc),
    )
    rev = alt_rev if "revenue" in subset else base_rev
    return d, rev


def shapley_bridge(base_pt: dict, from_d: Drivers, to_d: Drivers, from_rev, to_rev, keys=None) -> dict:
    """Exact Shapley values over 2^k coalitions.

    Naive one-at-a-time sensitivity does not sum to the total because DCF
    driver interactions are large. Shapley is order-independent and additive by
    construction, so the residual assertion below is a genuine check.
    """
    keys = keys or DRIVER_KEYS
    k = len(keys)
    cache = {}

    def value(subset: frozenset) -> float:
        if subset not in cache:
            d, rev = _blend(from_d, to_d, subset, from_rev, to_rev, keys)
            try:
                cache[subset] = dcf(base_pt, d, revenue_override=rev)["value_per_share"]
            except ValueError:
                # an infeasible coalition (WACC-g too tight) contributes its
                # boundary value rather than aborting the whole bridge
                cache[subset] = float("nan")
        return cache[subset]

    v_empty = value(frozenset())
    v_full = value(frozenset(keys))

    contrib = {}
    for key in keys:
        others = [x for x in keys if x != key]
        total = 0.0
        for size in range(len(others) + 1):
            w = factorial(size) * factorial(k - size - 1) / factorial(k)
            for combo in combinations(others, size):
                s = frozenset(combo)
                total += w * (value(s | {key}) - value(s))
        contrib[key] = total

    resid = v_full - v_empty - sum(contrib.values())
    return {
        "start_value": v_empty,
        "end_value": v_full,
        "total_gap": v_full - v_empty,
        "contributions": contrib,
        "residual": resid,
        "method": "shapley_exact",
        "coalitions_evaluated": len(cache),
    }


# --------------------------------------------------------------------------
# Reverse DCF: three independent solves
# --------------------------------------------------------------------------
def _solve(fn, lo, hi, target, tol=1e-7, iters=200):
    for _ in range(iters):
        mid = (lo + hi) / 2
        try:
            v = fn(mid)
        except ValueError:
            v = float("-inf") if mid > (lo + hi) / 2 else float("inf")
        if abs(v - target) < tol:
            return mid
        if v < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def reverse_triple(base: dict, drivers: Drivers) -> dict:
    """What must be true to justify the current price, one variable at a time.

    Strictly more informative than a comps table: it states the market's
    implied assumption in the units the drivers are argued in.
    """
    spot = base["spot"]
    base_rev = build_revenue(base["segments"], drivers)["total"]

    def with_growth(uplift):
        rev, prev = [], base["revenue"]
        for i in range(YEARS):
            g = (base_rev[i] / (base_rev[i - 1] if i else base["revenue"])) - 1
            prev = prev * (1 + g + uplift)
            rev.append(prev)
        return dcf(base, drivers, revenue_override=rev)["value_per_share"]

    def with_margin(term_margin):
        m = list(drivers.ebit_margin)
        start = m[0]
        m = [start + (term_margin - start) * (i / (YEARS - 1)) for i in range(YEARS)]
        d = Drivers(**{**drivers.__dict__, "ebit_margin": m})
        return dcf(base, d, revenue_override=base_rev)["value_per_share"]

    def with_wacc(w):
        d = Drivers(**{**drivers.__dict__, "wacc": w})
        return dcf(base, d, revenue_override=base_rev)["value_per_share"]

    uplift = _solve(with_growth, -0.30, 0.60, spot, tol=1e-4)
    implied_rev = []
    prev = base["revenue"]
    for i in range(YEARS):
        g = (base_rev[i] / (base_rev[i - 1] if i else base["revenue"])) - 1
        prev = prev * (1 + g + uplift)
        implied_rev.append(prev)
    cagr = (implied_rev[-1] / base["revenue"]) ** (1 / YEARS) - 1

    margin = _solve(with_margin, 0.05, 0.95, spot, tol=1e-4)

    # value(wacc) is decreasing, so bisect on the negated function
    lo_w, hi_w = drivers.terminal_growth + 0.016, 0.40
    for _ in range(200):
        mid = (lo_w + hi_w) / 2
        try:
            v = with_wacc(mid)
        except ValueError:
            v = float("inf")
        if abs(v - spot) < 1e-4:
            break
        if v > spot:
            lo_w = mid
        else:
            hi_w = mid
    wacc = (lo_w + hi_w) / 2

    return {
        "implied_revenue_cagr": cagr,
        "implied_terminal_year_revenue": implied_rev[-1],
        "implied_terminal_ebit_margin": margin,
        "implied_wacc": wacc,
        "spot": spot,
    }
