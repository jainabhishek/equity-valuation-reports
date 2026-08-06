"""Decision layer: probabilities, expected value, risk/reward, sizing, kill criteria.

Probabilities are integers in basis points summing to 10000 -- never floats --
and each carries an anchor naming what it is grounded in. Sizing is computed
through a constraint cascade and the binding constraint is published, so a
reader can see which limit actually set the number.
"""
from __future__ import annotations

# Illustrative book. This is a public research artefact, not a fund.
NAV = 1_000_000_000.0
RISK_BUDGET = 0.015      # max 1.5% of NAV at risk to the adverse case
CONCENTRATION_CAP = 0.05
KELLY_FRACTION = 0.25
ADV_LIMIT = 0.20         # may not exceed 20% of ADV over 5 days

# 30-day average dollar volume, $/day, as of 2026-08-04.
ADV_USD = {"GOOGL": 22.4e9, "NVDA": 41.8e9}

PROBS = {
    "GOOGL": {
        "bear": {"bp": 2500, "anchor": "consensus_dispersion", "justification": (
            "The depreciation catch-up arrives with no offsetting EBITDA margin expansion and "
            "Search ad coverage erodes faster than modelled. Held below the base case because "
            "Alphabet has beaten EPS in all eight reported quarters and Cloud is currently "
            "supply-constrained rather than demand-constrained.")},
        "base": {"bp": 4500, "anchor": "judgment", "justification": (
            "Modal because the arithmetic is close to mechanical: $844bn of cumulative capex "
            "over six years cannot be carried at 4.6% of revenue in D&A under any useful life "
            "Alphabet currently discloses. The uncertainty is timing and offsetting margin, "
            "not direction.")},
        "bull": {"bp": 3000, "anchor": "consensus_dispersion", "justification": (
            "Carries real weight because it embeds the market's own implied ~6.1% discount rate "
            "and the possibility that AI capex proves front-loaded rather than permanent. "
            "Thirty-nine analysts and a $427 median target sit closer to this case than to ours.")},
    },
    "NVDA": {
        "bear": {"bp": 2500, "anchor": "historical_base_rate", "justification": (
            "A digestion year of the kind semiconductor cycles have produced repeatedly, plus "
            "custom-ASIC share gain on incremental sockets and gross-margin compression from "
            "HBM and advanced packaging cost. A cycle, not a thesis break.")},
        "base": {"bp": 5000, "anchor": "consensus_dispersion", "justification": (
            "Our revenue path sits within the analyst range in every covered year, so this is "
            "genuinely the central expectation rather than a variant. The disagreement with the "
            "Street is on terminal margin, not near-term demand.")},
        "bull": {"bp": 2500, "anchor": "judgment", "justification": (
            "Rubin holds pricing, networking attach keeps climbing, and accelerated computing "
            "takes a larger share of a still-growing infrastructure budget. The width of this "
            "case against the bear case is the reason we carry no position.")},
    },
}

RATING = {
    "GOOGL": {
        "rating": "SHORT",
        "conviction": 2,
        "horizon_months": 18,
        "edge_type": "analytical",
        "edge_statement": (
            "No proprietary information. The edge is that a depreciation schedule built from "
            "disclosed capex vintages contradicts the EBIT margin the consensus feed carries, "
            "and that contradiction is checkable from public filings every ninety days."),
        "thesis": [
            {"kind": "What we think", "text":
             "The operating business is compounding above 20%. The reported earnings it produces "
             "are not the earnings the capex programme will leave behind."},
            {"kind": "Why it is not priced", "text":
             "Consensus holds D&A at 4.6% of revenue through 2030 while capex runs at 29.7%. "
             "Our vintage schedule reaches 13.2%."},
            {"kind": "What makes it work", "text":
             "D&A is disclosed quarterly. Every print showing it climb toward capex closes the "
             "gap. Next print 28 October 2026."},
        ],
        "kill_criteria": [
            {"id": "k1", "statement": "Alphabet extends disclosed server useful life beyond six years",
             "observable": "Property & equipment useful-life disclosure, FY2026 Form 10-K",
             "threshold": "> 6 years", "check_date": "2027-02-28", "action": "exit full",
             "note": "Extending life defers the entire catch-up and breaks the thesis outright."},
            {"id": "k2", "statement": "FY2027 capex guidance below $110bn",
             "observable": "Capex guidance, Q4 FY2026 earnings call",
             "threshold": "< $110bn", "check_date": "2027-02-05", "action": "cut half",
             "note": "A sharp step down means the build-out was front-loaded and FCF inflects early."},
            {"id": "k3", "statement": "D&A passes 9% of revenue while EBIT margin holds above 30%",
             "observable": "Depreciation / revenue and operating margin, quarterly",
             "threshold": "both true in one quarter", "check_date": "2027-07-31", "action": "cut half",
             "note": "Would mean EBITDA margin is expanding fast enough to absorb the charge."},
            {"id": "k4", "statement": "Cloud revenue growth below 25% for two consecutive quarters",
             "observable": "Google Cloud segment revenue growth, 10-Q",
             "threshold": "< 25% YoY x2", "check_date": "2027-04-30", "action": "review",
             "note": "Our supply-constrained framing would be wrong: demand, not capacity, binds."},
        ],
        "catalysts": [
            {"date": "2026-10-28", "confirmed": True, "event": "Q3 FY2026 results",
             "learn": "D&A/revenue trajectory, capex guide, Cloud growth and backlog", "tests": "k3, k4"},
            {"date": "2027-02-05", "confirmed": False, "event": "Q4 FY2026 results and Form 10-K",
             "learn": "FY2027 capex guidance and the useful-life disclosure", "tests": "k1, k2"},
            {"date": "2027-04-30", "confirmed": False, "event": "Q1 FY2027 results",
             "learn": "First clean read on whether the depreciation step-up is arriving", "tests": "k3"},
        ],
        "falsification": [
            "The strongest case against our own short: Alphabet has beaten EPS in eight consecutive "
            "quarters, Cloud is accelerating rather than decelerating, and the AI capex may be buying "
            "an option on a materially larger business rather than a commodity compute fleet. Our "
            "answer is that none of that is inconsistent with the depreciation arithmetic -- it "
            "changes the numerator, not the charge.",
            "Our valuation sits 54% below the Street's median target and below the lowest of 39 "
            "published targets. Either we are missing something 39 analysts can see, or the consensus "
            "feed carries a margin assumption nobody has re-derived. We think the latter, but the base "
            "rate on that judgement is not favourable and the position is sized accordingly.",
        ],
        "pre_mortem": (
            "Eighteen months out the position is down 30%. What happened: Alphabet extended server "
            "useful lives to eight years in the FY2026 10-K, cutting the annual depreciation charge by "
            "roughly a third at a stroke and pushing the catch-up beyond our horizon. At the same time "
            "Gemini monetisation lifted Search ad coverage instead of compressing it, and the complex "
            "re-rated on a lower discount rate as rates fell. We were right about the arithmetic and "
            "wrong about the accounting policy -- the one input management controls directly."),
    },
    "NVDA": {
        "rating": "NO POSITION",
        "conviction": 1,
        "horizon_months": 12,
        "edge_type": "none",
        "edge_statement": (
            "We have no edge here and the honest output is no position. Our revenue path sits inside "
            "the analyst range in every covered year, expected value is 3% above spot -- inside the "
            "noise -- and the scenario range spans $67 to $437. No defensible position size survives "
            "that spread."),
        "thesis": [
            {"kind": "What we think", "text":
             "Extraordinary economics: 64% EBIT margin, 2.6% capex intensity, $119bn of free cash "
             "flow. The business is not the question."},
            {"kind": "Why it is not priced", "text":
             "It is priced. Our base case is 10% below spot, our revenue path is inside the analyst "
             "range every year, and we hold no variant view."},
            {"kind": "What makes it work", "text":
             "Nothing currently observable resolves the terminal-margin question, which is where the "
             "entire disagreement sits."},
        ],
        "kill_criteria": [
            {"id": "k1", "statement": "Equity stakes in customers exceed 40% of revenue",
             "observable": "Equity securities (marketable + non-marketable) / TTM revenue",
             "threshold": "> 40%", "check_date": "2027-02-28", "action": "review",
             "note": "Currently 28.6%, up from ~3% a year ago. The cleanest tell on demand quality."},
            {"id": "k2", "statement": "Gross margin below 68% for two consecutive quarters",
             "observable": "GrossProfit / Revenues, quarterly",
             "threshold": "< 68% x2", "check_date": "2027-05-31", "action": "review",
             "note": "Would confirm the cost and mix compression the base case models."},
            {"id": "k3", "statement": "Inventory grows faster than guided forward revenue",
             "observable": "InventoryNet vs next-quarter revenue guidance",
             "threshold": "two consecutive quarters", "check_date": "2027-05-31", "action": "review",
             "note": "Inventory is $25.8bn and rising; it leads demand inflections both ways."},
        ],
        "catalysts": [
            {"date": "2026-08-26", "confirmed": False, "event": "Q2 FY2027 results",
             "learn": "Rubin ramp pricing, networking attach, China contribution", "tests": "k2"},
            {"date": "2026-11-18", "confirmed": False, "event": "Q3 FY2027 results",
             "learn": "Inventory and purchase commitments against the forward guide", "tests": "k3"},
            {"date": "2027-02-25", "confirmed": False, "event": "Q4 FY2027 results and Form 10-K",
             "learn": "Customer concentration and the full equity-stake disclosure", "tests": "k1"},
        ],
        "falsification": [
            "The case for owning it anyway: at 37.8x economic earnings for a business growing revenue "
            "85% at 64% operating margins the multiple is not obviously wrong, and our terminal-margin "
            "fade to 53.5% may be too aggressive for a company with this much architectural lock-in. "
            "If terminal margin holds at 60% the base case clears spot comfortably.",
            "The case for shorting it: $72.6bn of equity stakes in customers who use the proceeds to "
            "buy accelerators means some share of reported demand is self-funded, and that share is "
            "rising fast. We cannot size it from public disclosure, which is precisely why we will not "
            "take the other side either.",
        ],
        "pre_mortem": (
            "Twelve months out we have missed a double. What happened: Rubin shipped into a market "
            "still short of compute, networking attach kept climbing, and the terminal-margin debate "
            "never arrived because revenue grew fast enough to make it irrelevant on any horizon that "
            "mattered. We stood aside because our range was wide -- and a wide range is not the same "
            "thing as an unfavourable one."),
    },
}


def expected_value(scen, probs):
    return sum(scen[k] * probs[k]["bp"] / 10000 for k in ("bear", "base", "bull"))


def breakeven_bull(scen, probs, spot):
    """p_bull that makes EV equal spot, holding the bear:base ratio fixed."""
    pb, pu = probs["bear"]["bp"], probs["base"]["bp"]
    tot = pb + pu
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        rest = 1 - mid
        ev = scen["bear"] * rest * pb / tot + scen["base"] * rest * pu / tot + scen["bull"] * mid
        if ev < spot:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def size(ticker, scen, probs, spot, direction):
    """Constraint cascade. Every term is published so the binding limit is visible."""
    ev = expected_value(scen, probs)
    if direction == "SHORT":
        reward, risk = spot - ev, max(scen["bull"] - spot, 1e-9)
        p_win = (probs["bear"]["bp"] + probs["base"]["bp"]) / 10000
    else:
        reward, risk = ev - spot, max(spot - scen["bear"], 1e-9)
        p_win = (probs["base"]["bp"] + probs["bull"]["bp"]) / 10000
    downside_per_unit = risk / spot

    b = reward / risk if risk else 0.0
    kelly = (p_win * b - (1 - p_win)) / b if b > 0 else 0.0
    raw = max(KELLY_FRACTION * kelly, 0.0)
    liq = ADV_LIMIT * 5 * ADV_USD[ticker] / NAV
    vol = RISK_BUDGET / downside_per_unit if downside_per_unit else raw
    options = [("quarter-Kelly", raw), ("liquidity", liq), ("risk budget", vol),
               ("concentration cap", CONCENTRATION_CAP)]
    capped = min(v for _, v in options)
    binding = min(options, key=lambda kv: kv[1])[0]
    return {
        "expected_value": ev, "reward": reward, "risk": risk, "b": b, "p_win": p_win,
        "kelly_f": kelly, "size_raw": raw, "size_liquidity": liq, "size_risk_budget": vol,
        "size_concentration": CONCENTRATION_CAP,
        "position_size": round(capped * 400) / 400,
        "binding_constraint": binding, "risk_reward": b,
        "nav_basis": "illustrative $1bn book",
    }
