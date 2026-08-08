"""Assemble cases, run the DCF, produce the variant analysis, write results.json."""
from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import cases
import model
from model import Drivers

DATA = Path(__file__).parent / "data"
YEARS = model.YEARS


def anchored_capex(declared, delta, revenue, ytd, guidance=None):
    """Capex intensity path anchored on the best evidence available for year 1.

    Forecast year 1 is part history. At 2026-06-30, calendar 2026 is half
    reported: $80.6bn of Alphabet capex is a filed fact, not a forecast. The
    anchor is therefore chosen in this order:

      1. management guidance for the year, if it exists;
      2. otherwise reported fiscal-YTD + remaining quarters at the exit rate.

    Guidance ranks first because it is management telling us the answer for a
    year they are half way through, and because the extrapolation it replaces
    is only ever an assumption about the stub. For Alphabet the two differ by a
    lot: holding the $44.9bn Q2 exit quarter flat gives $170.4bn for calendar
    2026, against a guided $195-205bn. Freezing a quarterly figure that has
    risen for seven consecutive quarters is conservative when nobody has
    guided; it is simply wrong once somebody has.

    Later years fade to the declared terminal intensity, preserving the shape
    of the declared path. Terminal intensity stays a stated judgment about
    steady-state reinvestment; it is not rescaled by a year-1 revision.

    Scenario deltas move the forecast stub and the fade, never the reported
    portion -- bear and bull disagree about the future, not about what
    happened. Against a guided year the same deltas span the guided range:
    Alphabet's bear (+2.0% of stub revenue) lands near the top of $195-205bn
    and its bull (-2.5%) near the bottom, which is the right shape. Bear spends
    more and gets less; bull finds the build front-loaded.
    """
    ytd_capex = ytd["capex"]["val"]
    ytd_revenue = ytd["revenue"]["val"]
    stub_revenue = max(revenue[0] - ytd_revenue, 0.0)
    if guidance is not None:
        anchor = (guidance["low"] + guidance["high"]) / 2
    else:
        anchor = ytd_capex + ytd["quarters_remaining"] * ytd["exit_quarter_capex"]["val"]
    y1_capex = anchor + delta * stub_revenue
    y1 = y1_capex / revenue[0]

    terminal = declared[-1] + delta
    steps = [declared[i] - declared[i + 1] for i in range(len(declared) - 1)]
    total = sum(steps)
    weights = ([s / total for s in steps] if total
               else [1.0 / len(steps)] * len(steps))
    span = y1 - terminal
    path = [y1]
    for w in weights:
        path.append(path[-1] - span * w)
    return path


def check_year_one_capex(ticker, scenario, rows, ytd, guidance=None):
    """Year 1 cannot contradict what is already known about year 1.

    Two ways to get this wrong, both of which have actually happened here:

      * forecasting less than the company has already spent. A full-year 2026
        figure of $145.1bn against $80.6bn of reported first-half spend implied
        a second half below the first quarter, which nothing had guided to and
        no reviewer had queried.
      * forecasting outside the range management has guided to. The exit-rate
        anchor that fixed the first defect produced $170.4bn against a guided
        $195-205bn, and shipped, because nothing in the build looked at
        guidance at all.

    The base case must sit inside the guided range. Bear and bull are allowed
    outside it -- disagreeing with guidance is what a scenario is for -- but
    the base case claiming a number management has ruled out is an error, not
    a view.
    """
    y1, actual = rows[0]["capex"], ytd["capex"]["val"]
    if y1 < actual:
        raise RuntimeError(
            f"{ticker}: forecast year-1 capex {y1/1e9:,.1f}bn is below reported fiscal-YTD "
            f"capex of {actual/1e9:,.1f}bn at {ytd['capex']['start']}..(Q{ytd['quarters_elapsed']}). "
            "The year-1 anchor is wrong."
        )
    out = {"year_one_capex": y1, "ytd_actual": actual,
           "implied_remaining_quarterly": (y1 - actual) / max(ytd["quarters_remaining"], 1),
           "exit_quarter": ytd["exit_quarter_capex"]["val"], "guided": guidance is not None}
    out["vs_exit_quarter"] = out["implied_remaining_quarterly"] / out["exit_quarter"] - 1

    if guidance is not None:
        if guidance["low"] < actual:
            raise RuntimeError(
                f"{ticker}: guided full-year capex low end {guidance['low']/1e9:,.1f}bn is below "
                f"reported fiscal-YTD capex of {actual/1e9:,.1f}bn. The guidance record is stale "
                f"or mis-keyed -- check CAPEX_GUIDANCE against {guidance['source']}."
            )
        if scenario == "base" and not (guidance["low"] <= y1 <= guidance["high"]):
            raise RuntimeError(
                f"{ticker}: base-case year-1 capex {y1/1e9:,.1f}bn falls outside management "
                f"guidance of {guidance['low']/1e9:,.0f}-{guidance['high']/1e9:,.0f}bn "
                f"({guidance['source']}). The base case may not contradict guidance."
            )
        out.update(guidance_low=guidance["low"], guidance_high=guidance["high"],
                   guidance_source=guidance["source"], guidance_as_of=guidance["as_of"],
                   inside_guidance=guidance["low"] <= y1 <= guidance["high"],
                   exit_rate_alternative=(actual + ytd["quarters_remaining"]
                                          * ytd["exit_quarter_capex"]["val"]))
    return out


def check_year_one_revenue(ticker, rows, ytd, guidance):
    """Year 1 revenue must clear what is already reported plus what is guided.

    The capex anchor has a floor; revenue did not, and the same class of defect
    is available on this side of the model. Nvidia's fiscal 2027 is a quarter
    reported ($81.6bn) and a quarter guided ($91.0bn +/- 2%), which fixes more
    than a third of the year before the segment build says anything. A forecast
    below that sum is not a bearish view, it is arithmetic that has already
    been falsified.
    """
    if guidance is None:
        return None
    y1 = rows[0]["revenue"]
    reported = ytd["revenue"]["val"]
    if ytd["quarters_elapsed"] + 1 != guidance["quarter"]:
        raise RuntimeError(
            f"{ticker}: revenue guidance is for Q{guidance['quarter']} but {ytd['quarters_elapsed']} "
            f"quarter(s) are reported, so the guided quarter is not the next one. "
            f"Check REVENUE_GUIDANCE against {guidance['source']}."
        )
    lo = guidance["mid"] * (1 - guidance["tolerance"])
    hi = guidance["mid"] * (1 + guidance["tolerance"])
    floor = reported + lo
    if y1 < floor:
        raise RuntimeError(
            f"{ticker}: forecast year-1 revenue {y1/1e9:,.1f}bn is below reported "
            f"{reported/1e9:,.1f}bn plus the low end of guidance {lo/1e9:,.1f}bn. The remaining "
            f"{ytd['quarters_remaining'] - 1} quarter(s) would have to be negative."
        )
    remaining_q = ytd["quarters_remaining"] - 1
    stub = y1 - reported - guidance["mid"]
    return {
        "year_one_revenue": y1, "reported": reported, "reported_quarters": ytd["quarters_elapsed"],
        "guided_mid": guidance["mid"], "guided_low": lo, "guided_high": hi,
        "guided_quarter": guidance["quarter"], "guided_period_end": guidance["period_end"],
        "covered": (reported + guidance["mid"]) / y1,
        "stub": stub, "stub_quarters": remaining_q,
        "stub_per_quarter": stub / remaining_q if remaining_q else None,
        "stub_vs_guided_quarter": (stub / remaining_q / guidance["mid"] - 1) if remaining_q else None,
        "source": guidance["source"], "as_of": guidance["as_of"], "caveat": guidance["caveat"],
    }


def check_year_one_segments(ticker, scenario, segment_paths, ytd, actuals):
    """No segment may forecast a stub below what its own exit quarter printed.

    The consolidated checks above cannot see a mix error. Forecast 2026 Cloud of
    $91.0bn against $44.8bn reported implied $23.1bn in each remaining quarter
    against a $24.8bn exit quarter -- a sequential decline in the fastest-growing
    segment in the company -- while consolidated 2026 revenue looked entirely
    reasonable, because other segments were forecast above their exit rates and
    absorbed it. A total can be right for wrong reasons. Each part cannot.

    The floor is the exit quarter less SEGMENT_DECLINE_TOLERANCE, not the exit
    quarter itself: segments do have soft quarters, and a zero-tolerance floor
    turns ordinary noise into a build failure. Declines beyond that need an entry
    in SEGMENT_DECLINE_EXEMPT saying why, which is a sentence somebody has to
    write rather than a number that quietly passes.

    Applied to every scenario. A bear case is entitled to a pessimistic view of
    the future; it is not entitled to a pessimistic view of a quarter that has
    already been reported.
    """
    if actuals is None:
        return None
    if actuals["fiscal_year"] != cases.FIRST_YEAR[ticker]:
        raise RuntimeError(
            f"{ticker}: SEGMENT_ACTUALS is keyed to fiscal year {actuals['fiscal_year']} but the "
            f"first forecast year is {cases.FIRST_YEAR[ticker]}."
        )
    quarters = actuals["quarters"]
    if len(quarters) != ytd["quarters_elapsed"]:
        raise RuntimeError(
            f"{ticker}: SEGMENT_ACTUALS carries {len(quarters)} quarter(s) but "
            f"{ytd['quarters_elapsed']} are reported in the consolidated YTD. The segment record "
            "is stale; add the missing quarter from its earnings release."
        )

    # Two reconciliations, because they catch different mistakes.
    #
    # First, within each quarter: the segment lines plus hedging must sum to the
    # total printed on the same page. Without this a single mis-keyed segment
    # passes silently -- the totals still tie to XBRL, because the total is a
    # separate field nobody touched. That is the same shape of error as the Cloud
    # defect this function exists to catch, one level further down, and the first
    # draft of this check had it.
    for q in quarters:
        seg_sum = sum(q["segments"].values()) + q.get("hedging", 0.0)
        if abs(seg_sum - q["total_reported"]) > 1:      # $1m, i.e. a rounding unit
            raise RuntimeError(
                f"{ticker}: segment lines for {q['period_end']} sum to ${seg_sum:,.0f}m plus "
                f"hedging, against a printed total of ${q['total_reported']:,.0f}m "
                f"(accn {q['accn']}). A segment is mis-keyed."
            )

    # Second, across quarters: the recorded totals must reconcile to the
    # consolidated YTD already in base_year.json, which comes from XBRL. Two
    # independent sources for the same fact; if they disagree, one was keyed wrong.
    recorded_total = sum(q["total_reported"] for q in quarters) * 1e6
    if abs(recorded_total - ytd["revenue"]["val"]) > 1e6:
        raise RuntimeError(
            f"{ticker}: SEGMENT_ACTUALS quarterly totals sum to {recorded_total/1e9:,.3f}bn but "
            f"consolidated fiscal-YTD revenue is {ytd['revenue']['val']/1e9:,.3f}bn "
            f"(accn {ytd['revenue']['accn']}). One of the two is mis-keyed."
        )

    remaining = ytd["quarters_remaining"]
    exempt = cases.SEGMENT_DECLINE_EXEMPT.get(ticker, {})
    rows, worst = [], None
    for seg in segment_paths:
        reported = sum(q["segments"].get(seg, 0.0) for q in quarters) * 1e6
        exit_q = quarters[-1]["segments"].get(seg, 0.0) * 1e6
        y1 = segment_paths[seg][0]
        if y1 < reported:
            raise RuntimeError(
                f"{ticker} [{scenario}]: forecast {cases.FIRST_YEAR[ticker]} {seg} revenue of "
                f"{y1/1e9:,.1f}bn is below the {reported/1e9:,.1f}bn already reported through "
                f"Q{ytd['quarters_elapsed']}."
            )
        implied = (y1 - reported) / remaining if remaining else None
        vs_exit = (implied / exit_q - 1) if (implied is not None and exit_q) else None
        rows.append({"segment": seg, "year_one": y1, "reported": reported, "exit_quarter": exit_q,
                     "implied_per_quarter": implied, "vs_exit_quarter": vs_exit,
                     "exempt": seg in exempt})
        if vs_exit is not None and (worst is None or vs_exit < worst["vs_exit_quarter"]):
            worst = rows[-1]
        if vs_exit is not None and vs_exit < -cases.SEGMENT_DECLINE_TOLERANCE and seg not in exempt:
            raise RuntimeError(
                f"{ticker} [{scenario}]: forecast {cases.FIRST_YEAR[ticker]} {seg} revenue of "
                f"{y1/1e9:,.1f}bn against {reported/1e9:,.1f}bn reported implies "
                f"{implied/1e9:,.1f}bn in each of the {remaining} remaining quarter(s), "
                f"{vs_exit:+.1%} against the {exit_q/1e9:,.1f}bn exit quarter "
                f"({quarters[-1]['period_end']}, accn {quarters[-1]['accn']}). That is a sequential "
                f"decline the reported quarters do not support. Either raise the year-1 driver or "
                f"add '{seg}' to SEGMENT_DECLINE_EXEMPT['{ticker}'] with the reason."
            )
    return {"rows": rows, "worst": worst, "reported_quarters": ytd["quarters_elapsed"],
            "remaining_quarters": remaining, "tolerance": cases.SEGMENT_DECLINE_TOLERANCE,
            "sources": [{"period_end": q["period_end"], "accn": q["accn"], "form": q["form"]}
                        for q in quarters]}


def make_drivers(ticker, scenario, base_revenue, ytd):
    """Build a Drivers object, deriving EBIT margin from the depreciation schedule."""
    spec = cases.SPEC[ticker]
    d = copy.deepcopy(spec["drivers"]["base"])
    adj = spec["drivers"].get(scenario, {}) if scenario != "base" else {}

    segs = copy.deepcopy(d["segments"])
    # apply scenario deltas to the named drivers that carry the thesis
    for seg, mapping in spec["scenario_deltas"].items():
        for i in range(0, len(mapping), 2):
            driver, key = mapping[i], mapping[i + 1]
            if key in adj:
                segs[seg][driver] = [v + adj[key] for v in segs[seg][driver]]

    ebitda_margin = [m + adj.get("ebitda_margin_delta", 0.0) for m in d["ebitda_margin"]]
    tg = adj.get("terminal_growth", d["terminal_growth"])
    wacc = adj.get("wacc", d["wacc"])

    # Revenue first: it is segment-driven and does not depend on capex, so the
    # capex path can then be anchored against the year-1 revenue it implies.
    probe = Drivers(
        segments=segs, ebit_margin=[0.0] * YEARS, tax_rate=d["tax_rate"],
        da_pct_revenue=[0.0] * YEARS, capex_pct_revenue=[0.0] * YEARS,
        nwc_pct_revenue=d["nwc_pct_revenue"], terminal_growth=tg, wacc=wacc, label=scenario,
    )
    rev = model.build_revenue(cases.SPEC[ticker]["base_segments"], probe)["total"]
    capex_pct = anchored_capex(d["capex_pct_revenue"], adj.get("capex_delta", 0.0), rev, ytd,
                               guidance=cases.CAPEX_GUIDANCE.get(ticker))

    capex_abs = [rev[i] * capex_pct[i] / 1e9 for i in range(YEARS)]
    da_abs = cases.depreciation_path(ticker, capex_abs, cases.FIRST_YEAR[ticker], YEARS)
    da_pct = [da_abs[i] * 1e9 / rev[i] for i in range(YEARS)]
    ebit_margin = [ebitda_margin[i] - da_pct[i] for i in range(YEARS)]

    return Drivers(
        segments=segs, ebit_margin=ebit_margin, tax_rate=d["tax_rate"],
        da_pct_revenue=da_pct, capex_pct_revenue=capex_pct,
        nwc_pct_revenue=d["nwc_pct_revenue"], terminal_growth=tg, wacc=wacc, label=scenario,
        notes={"ebitda_margin": ebitda_margin, "da_abs_bn": da_abs},
    )


def base_point(ticker, by):
    b = by[ticker]
    spec = cases.SPEC[ticker]
    return {
        "segments": spec["base_segments"],
        "revenue": sum(spec["base_segments"].values()),
        "diluted_shares": b["diluted_shares_m"] * 1e6,
        "spot": b["spot"],
        "bridge": {
            "cash_and_marketable": b["balance_sheet"]["cash_and_marketable"],
            "equity_investments": b["balance_sheet"]["equity_investments"],
            "debt": b["balance_sheet"]["debt"],
            "leases": b["balance_sheet"]["leases"],
            "preferred": b["balance_sheet"].get("preferred", 0.0),
        },
    }


def eps_variant(ticker, base_dv, est, fy0, diluted_shares, tax_rate):
    """Restate the depreciation variant in EPS, because EPS is what analysts publish.

    The memo has been stating its variant as "consensus carries D&A at 4.6% of
    revenue". That is true of the feed and it is the wrong thing to lean on. The
    feed's EBIT margin is 32.48% in every single forecast year and its implied
    D&A is 4.62% in every single forecast year, to four significant figures --
    EBIT growth equals revenue growth to a decimal place in all five. No panel of
    forty analysts produces that. It is a vendor applying a constant margin to a
    revenue consensus, so disagreeing with it is not disagreeing with anybody.

    The feed's EPS line is different in kind: it moves independently year to
    year and it carries the largest analyst cohort of any field. So: take the
    Street's own revenue and EBITDA, substitute our depreciation schedule for
    theirs, and read off the EPS it implies. If we are right about depreciation
    and they are right about everything else, that is roughly where EPS lands --
    and unlike a D&A ratio, it is checked against a printed number four times a
    year.

    Only computed where EPS_CORROBORATION says the feed's EPS is sound. Nvidia
    has no entry: its feed net income exceeds EBIT in five forecast years, and a
    variant stated against an incoherent number would be worse than no variant.
    """
    corr = cases.EPS_CORROBORATION.get(ticker)
    if corr is None:
        return None
    by_fy = {e["fy"]: e for e in est}
    rows = []
    for i in range(YEARS):
        fy = fy0 + i
        e = by_fy.get(fy)
        if not e or not e.get("ebitda_avg") or not e.get("eps_avg"):
            continue
        street_rev, street_ebit = e["revenue_avg"], e["ebit_avg"]
        street_da = e["ebitda_avg"] - street_ebit
        our_da = base_dv.da_pct_revenue[i] * street_rev
        our_ebit = e["ebitda_avg"] - our_da
        eps_delta = (street_ebit - our_ebit) * (1 - tax_rate[i]) / diluted_shares
        rows.append({
            "fy": fy,
            "street_eps": e["eps_avg"], "n_eps": e.get("n_eps"),
            "street_da": street_da, "street_da_pct": street_da / street_rev,
            "our_da_pct": base_dv.da_pct_revenue[i], "our_da_on_street_revenue": our_da,
            "street_ebit_margin": street_ebit / street_rev,
            "restated_ebit_margin": our_ebit / street_rev,
            "eps_delta": eps_delta,
            "restated_eps": e["eps_avg"] - eps_delta,
            "eps_delta_pct": -eps_delta / e["eps_avg"] if e["eps_avg"] else None,
        })
    flat_ebit = len({round(r["street_ebit_margin"], 4) for r in rows}) == 1 if rows else False
    flat_da = len({round(r["street_da_pct"], 4) for r in rows}) == 1 if rows else False
    headline = next((r for r in rows if r["fy"] == corr["fiscal_year"]), None)
    if headline is None:
        raise RuntimeError(
            f"{ticker}: EPS_CORROBORATION is keyed to fiscal year {corr['fiscal_year']}, which the "
            f"consensus feed does not carry an estimate for. The corroboration record is stale."
        )
    if not (corr["reported_low"] <= headline["street_eps"] <= corr["reported_high"] * 1.05):
        raise RuntimeError(
            f"{ticker}: feed {corr['fiscal_year']}E EPS of {headline['street_eps']:.2f} is outside "
            f"the {corr['reported_low']:.2f}-{corr['reported_high']:.2f} range independently "
            f"reported for Street consensus. The feed's EPS is no longer corroborated, so the "
            f"variant may not be stated against it -- re-check EPS_CORROBORATION."
        )
    return {
        "rows": rows,
        "headline": headline,
        "corroboration": corr,
        "feed_margin_is_constant": flat_ebit and flat_da,
        "note": ("The feed's EBIT margin and implied D&A are identical in every forecast year, "
                 "which is a vendor derivation rather than an analyst forecast. The EPS line is "
                 "not: it is the field with the largest cohort and it is what the variant is "
                 "stated against."),
    }


def wacc_sensitivity(bp, base_dv, base_res, reverse, grid=(0.0650, 0.0700, 0.0757, 0.0800,
                                                            0.0850, 0.0875, 0.0900, 0.0950)):
    """Value per share across the discount rate, published rather than implied.

    Terminal value is ~89% of enterprise value here, so the discount rate is not
    one assumption among many: it is most of the answer. The base case uses a
    CAPM build of 8.75%; widely published estimates of Alphabet's WACC sit near
    7.5%, and the reverse DCF says the market is discounting at ~6.1%. Those are
    large differences and they belong in a table the reader can look at, not in
    a single number in a footnote.

    This is disclosure, not a change of view. 8.75% remains the base case. But a
    memo whose conclusion moves by a third across the range of defensible
    discount rates should say so, because a reader who prefers 7.5% is not
    disagreeing with the depreciation work at all -- they are disagreeing with
    one input, and they are entitled to know what it is worth.
    """
    out = []
    for w in sorted(set(grid) | {base_dv.wacc}):
        dv = replace(base_dv, wacc=w)
        try:
            r = model.dcf(bp, dv)
        except ValueError:      # WACC - g below the stability floor
            continue
        vps = r["value_per_share"]
        out.append({
            "wacc": w,
            "value_per_share": vps,
            "vs_base": vps / base_res["value_per_share"] - 1,
            "vs_spot": vps / bp["spot"] - 1,
            "tv_pct_ev": r["tv_pct_ev"],
            "is_base": abs(w - base_dv.wacc) < 1e-9,
            "note": ("base case, CAPM build" if abs(w - base_dv.wacc) < 1e-9
                     else "published third-party WACC estimates cluster here" if w == 0.0757
                     else None),
        })
    return {"grid": out, "base_wacc": base_dv.wacc,
            "market_implied_wacc": reverse["implied_wacc"],
            "terminal_growth": base_dv.terminal_growth,
            "tv_pct_ev": base_res["tv_pct_ev"]}


def main():
    by = json.loads((DATA / "base_year.json").read_text())
    cons = json.loads((DATA / "consensus.json").read_text())
    out = {}

    for ticker in ("GOOGL", "NVDA"):
        bp = base_point(ticker, by)
        fy0 = cases.FIRST_YEAR[ticker]
        est = cons[ticker]["estimates"]
        ytd = by[ticker]["ytd"]

        scen = {}
        for s in ("bear", "base", "bull"):
            dv = make_drivers(ticker, s, bp["revenue"], ytd)
            scen[s] = {"drivers": dv, "result": model.dcf(bp, dv)}
        guide = cases.CAPEX_GUIDANCE.get(ticker)
        if guide is not None and guide["fiscal_year"] != fy0:
            raise RuntimeError(
                f"{ticker}: CAPEX_GUIDANCE is keyed to fiscal year {guide['fiscal_year']} but the "
                f"first forecast year is {fy0}. Guidance for the wrong year would anchor year 1 "
                "on a figure that does not describe it."
            )
        capex_anchor = {s: check_year_one_capex(ticker, s, v["result"]["rows"], ytd, guide)
                        for s, v in scen.items()}
        rev_guide = cases.REVENUE_GUIDANCE.get(ticker)
        revenue_anchor = {s: check_year_one_revenue(ticker, v["result"]["rows"], ytd, rev_guide)
                          for s, v in scen.items()}
        seg_actuals = cases.SEGMENT_ACTUALS.get(ticker)
        segment_anchor = {
            s: check_year_one_segments(
                ticker, s, model.build_revenue(bp["segments"], v["drivers"])["by_segment"],
                ytd, seg_actuals)
            for s, v in scen.items()
        }

        base_dv = scen["base"]["drivers"]
        base_res = scen["base"]["result"]

        street = model.street_case(bp, base_dv, est, fy0)
        variant = model.variant_table(base_res, base_dv, est, fy0)

        # Shapley: from the Street-calibrated case to ours.
        street_margin = street["ebit_margin_path"]
        street_dv = Drivers(
            segments=base_dv.segments, ebit_margin=street_margin, tax_rate=base_dv.tax_rate,
            da_pct_revenue=street["da_pct_revenue_path"], capex_pct_revenue=base_dv.capex_pct_revenue,
            nwc_pct_revenue=base_dv.nwc_pct_revenue, terminal_growth=base_dv.terminal_growth,
            wacc=base_dv.wacc, label="street",
        )
        # da_pct_revenue is an attributable driver, not a carried field: the
        # gap between the Street's flat depreciation and our vintage schedule
        # is the thesis, so the bridge has to price it separately from margin.
        bridge = model.shapley_bridge(
            bp, street_dv, base_dv, street["revenue_path"], base_res["revenue_path"],
            keys=["revenue", "ebitda_margin", "da_pct_revenue", "capex_pct_revenue",
                  "nwc_pct_revenue", "wacc", "terminal_growth"],
        )

        rev_triple = model.reverse_triple(bp, base_dv)

        out[ticker] = {
            "spot": bp["spot"],
            "first_year": fy0,
            "diluted_shares": bp["diluted_shares"],
            "bridge_inputs": bp["bridge"],
            "base_revenue": bp["revenue"],
            "scenarios": {
                s: {
                    "value_per_share": v["result"]["value_per_share"],
                    "enterprise_value": v["result"]["enterprise_value"],
                    "equity_value": v["result"]["equity_value"],
                    "tv_pct_ev": v["result"]["tv_pct_ev"],
                    "wacc": v["drivers"].wacc,
                    "terminal_growth": v["drivers"].terminal_growth,
                    "rows": v["result"]["rows"],
                    "ebitda_margin": v["drivers"].notes["ebitda_margin"],
                    "da_abs_bn": v["drivers"].notes["da_abs_bn"],
                    "revenue_path": v["result"]["revenue_path"],
                    "segment_paths": model.build_revenue(bp["segments"], v["drivers"])["by_segment"],
                }
                for s, v in scen.items()
            },
            "street_case": {
                "value_per_share": street["value_per_share"],
                "revenue_path": street["revenue_path"],
                "ebit_margin_path": street["ebit_margin_path"],
                "da_pct_revenue_path": street["da_pct_revenue_path"],
                "carried_fields": street["carried_fields"],
                "extrapolated_years": street["extrapolated_years"],
                "tv_pct_ev": street["tv_pct_ev"],
            },
            "variant": variant,
            "bridge": bridge,
            "reverse": rev_triple,
            "capex_anchor": capex_anchor,
            "capex_guidance": guide,
            "revenue_anchor": revenue_anchor,
            "revenue_guidance": rev_guide,
            "segment_anchor": segment_anchor,
            "eps_variant": eps_variant(ticker, base_dv, est, fy0, bp["diluted_shares"],
                                       base_dv.tax_rate),
            "wacc_sensitivity": wacc_sensitivity(bp, base_dv, base_res, rev_triple),
            "ytd": ytd,
            "consensus_price_target": cons[ticker]["price_target"],
        }

        r = out[ticker]
        print(f"\n{'=' * 78}\n{ticker}   spot ${bp['spot']:.2f}\n{'=' * 78}")
        for s in ("bear", "base", "bull"):
            v = r["scenarios"][s]["value_per_share"]
            print(f"  {s:<6} ${v:>8,.2f}   ({v / bp['spot'] - 1:+.1%})   TV {r['scenarios'][s]['tv_pct_ev']:.0%} of EV")
        print(f"  street-calibrated  ${street['value_per_share']:>8,.2f}   ({street['value_per_share'] / bp['spot'] - 1:+.1%})")
        print(f"  Street price target ${cons[ticker]['price_target']['consensus']:.2f}")
        print(f"\n  reverse DCF — the market is paying for EITHER:")
        print(f"    revenue CAGR of {rev_triple['implied_revenue_cagr']:.1%}")
        print(f"    terminal EBIT margin of {rev_triple['implied_terminal_ebit_margin']:.1%}")
        print(f"    WACC of {rev_triple['implied_wacc']:.2%}")
        print(f"\n  value bridge, street-calibrated -> ours  (${bridge['start_value']:.2f} -> ${bridge['end_value']:.2f})")
        for k, v in sorted(bridge["contributions"].items(), key=lambda kv: -abs(kv[1])):
            print(f"    {k:<22} {v:>+8.2f}")
        print(f"    {'residual':<22} {bridge['residual']:>+8.4f}   ({bridge['coalitions_evaluated']} coalitions)")
        print(f"\n  variant vs Street (revenue):")
        for v in r["variant"]:
            flag = "" if v["inside_range"] else "  OUTSIDE RANGE"
            print(f"    {v['fy']}  ours ${v['ours'] / 1e9:>7,.0f}bn  street ${v['street_avg'] / 1e9:>7,.0f}bn"
                  f"  {v['delta_pct']:>+6.1%}  n={v['n_analysts']:<3}{flag}")

    (DATA / "results.json").write_text(json.dumps(out, indent=2, default=str))
    print("\nwrote data/results.json")


if __name__ == "__main__":
    main()
