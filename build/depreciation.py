"""Vintage depreciation roll-forward.

The core Alphabet question is whether a 32.5% EBIT margin survives $130bn+ of
annual capex. Reported D&A lags capex badly during a build-out, so the only way
to answer it is to depreciate each capex vintage over its useful life and let
the schedule catch up on its own.

The model is calibrated against reported D&A before it is used to forecast: if
it cannot reproduce history it does not get to make a claim about the future.
"""
from __future__ import annotations

import sec
import series


def annual_series(ticker, key, chains=None):
    """Annual totals from the quarterly series (sums of four quarters)."""
    chain = (chains or series.CHAINS)[key]
    tag, q = series.first_tag(ticker, chain)
    if not q:
        return {}, None
    by_year = {}
    for end, row in q.items():
        by_year.setdefault(end.year if hasattr(end, "year") else int(str(end)[:4]), []).append(row["val"])
    return {y: sum(v) for y, v in by_year.items() if len(v) == 4}, tag


def schedule(capex_by_year: dict[int, float], life: float, start_year: int, end_year: int,
             opening_base: float | None = None, opening_remaining_life: float | None = None):
    """D&A per year from straight-line depreciation of each capex vintage.

    opening_base carries the undepreciated balance of pre-history capex so the
    schedule does not start from zero.
    """
    out = {}
    for y in range(start_year, end_year + 1):
        d = 0.0
        for v, cap in capex_by_year.items():
            if v <= y < v + life:
                # half-year convention in the vintage year
                d += cap / life * (0.5 if v == y else 1.0)
        if opening_base and opening_remaining_life and y < start_year + opening_remaining_life:
            d += opening_base / opening_remaining_life
        out[y] = d
    return out


def calibrate(ticker: str, lives=(3, 4, 5, 6, 8)):
    """Find the useful life that best reproduces reported D&A."""
    capex, capex_tag = annual_series(ticker, "capex")
    if not capex:
        tag, q = series.first_tag(ticker, ["PaymentsToAcquireProductiveAssets"])
        by_year = {}
        for end, row in q.items():
            by_year.setdefault(end.year, []).append(row["val"])
        capex = {y: sum(v) for y, v in by_year.items() if len(v) == 4}
        capex_tag = tag
    da, da_tag = annual_series(ticker, "da")

    common = sorted(set(capex) & set(da))
    if len(common) < 3:
        return {"error": "insufficient overlapping history", "capex": capex, "da": da}

    fit = []
    for life in lives:
        # opening base sized so that year-1 modelled D&A matches year-1 actual
        y0 = common[0]
        sched = schedule(capex, life, y0, common[-1])
        gap = da[y0] - sched[y0]
        opening = max(gap * life, 0.0)
        sched = schedule(capex, life, y0, common[-1], opening_base=opening, opening_remaining_life=life)
        err = sum(abs(sched[y] - da[y]) / da[y] for y in common) / len(common)
        fit.append({"life": life, "mean_abs_pct_error": err, "opening_base": opening,
                    "modelled": {y: sched[y] for y in common}})
    fit.sort(key=lambda f: f["mean_abs_pct_error"])
    return {"capex": capex, "capex_tag": capex_tag, "da": da, "da_tag": da_tag,
            "years": common, "fits": fit, "best": fit[0]}


if __name__ == "__main__":
    for t in ("GOOGL", "NVDA"):
        r = calibrate(t)
        print(f"\n{'=' * 74}\n{t} depreciation calibration\n{'=' * 74}")
        if "error" in r:
            print(" ", r["error"])
            print("  capex years:", sorted(r["capex"]), " da years:", sorted(r["da"]))
            continue
        print(f"capex tag: {r['capex_tag']}   D&A tag: {r['da_tag']}")
        print("\n{:<8}{:>14}{:>14}".format("year", "capex $bn", "D&A actual $bn"))
        for y in r["years"]:
            print("{:<8}{:>14,.1f}{:>14,.1f}".format(y, r["capex"][y] / 1e9, r["da"][y] / 1e9))
        print("\n{:<8}{:>22}".format("life", "mean abs % error"))
        for f in r["fits"]:
            print("{:<8}{:>21.1f}%".format(f["life"], f["mean_abs_pct_error"] * 100))
        b = r["best"]
        print(f"\nbest fit: {b['life']}-year life, opening base ${b['opening_base'] / 1e9:,.1f}bn")
        print("{:<8}{:>14}{:>14}".format("year", "modelled", "actual"))
        for y in r["years"]:
            print("{:<8}{:>14,.1f}{:>14,.1f}".format(y, b["modelled"][y] / 1e9, r["da"][y] / 1e9))
