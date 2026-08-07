"""Assemble cases, run the DCF, produce the variant analysis, write results.json."""
from __future__ import annotations

import copy
import json
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
