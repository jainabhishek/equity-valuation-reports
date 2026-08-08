"""Decision layer: probabilities, expected value, and conditional action rules.

Probabilities are integers in basis points summing to 10000 -- never floats --
and each carries an anchor naming what it is grounded in.  This public research
artifact does not recommend position sizes: borrow, carry, factor, squeeze and
portfolio constraints are not available here.
"""
from __future__ import annotations

PROBS = {
    "GOOGL": {
        "bear": {"bp": 2500, "anchor": "conditional_eps_revision", "justification": (
            "FY2027 D&A rises faster than EBITDA and reported EPS lands near $13.70. A 20x "
            "multiple produces a $273.91 adverse operating outcome for the shares.")},
        "base": {"bp": 5000, "anchor": "wait_for_proof", "justification": (
            "The next filing does not yet establish a clean negative revision cycle. FY2027 EPS "
            "holds near $14.55 and a 23x multiple produces $334.68, below spot but insufficient "
            "to short without borrow, crowding, option and hedge evidence.")},
        "bull": {"bp": 2500, "anchor": "ebitda_offset", "justification": (
            "Revenue and EBITDA margin absorb the depreciation step-up, FY2027 EPS reaches "
            "$15.32 and a 26x multiple produces $398.41. This is the uncapped-side risk that "
            "precludes mechanical short sizing.")},
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
        "rating": "WAIT FOR PROOF",
        "conviction": 0,
        "horizon_months": 18,
        "edge_type": "conditional analytical",
        "edge_statement": (
            "The only actionable variant is a FY2027 EPS revision caused by placed-in-service D&A "
            "rising faster than EBITDA. The available vendor snapshot is a conflicting reference, "
            "not canonical consensus; valuation and implementation evidence remain open."),
        "thesis": [
            {"kind": "What we think", "text":
             "The D&A step-up is real, but it matters to the stock only if revenue and EBITDA fail "
             "to offset it and FY2027 EPS estimates revise lower."},
            {"kind": "Why it is not priced", "text":
             "A vendor snapshot shows FY2027 EPS at $15.01, above rather than bracketed by the "
             "model's $13.70-$15.32 range. The source conflict must be resolved before the gap is "
             "treated as a tradeable consensus revision."},
            {"kind": "What makes it work", "text":
             "A future filing must show D&A/revenue tracking above the model while EBITDA margin "
             "does not compensate, followed by broad FY2027 EPS revisions and a cleared short "
             "implementation ledger."},
        ],
        "kill_criteria": [
            {"id": "k1", "statement": "EBITDA offsets the D&A step-up",
             "observable": "Revenue, EBITDA and D&A in the next reported filing",
             "threshold": "FY2027 EPS run-rate at or above $15.32", "check_date": "next filing",
             "action": "do not short",
             "note": "The causal thesis fails if operating leverage absorbs the accounting charge."},
            {"id": "k2", "statement": "Capex remains high but EPS estimates do not revise lower",
             "observable": "Company guidance plus canonical broker consensus revisions",
             "threshold": "No broad negative FY2027 EPS revision after the filing",
             "check_date": "post-filing revision window", "action": "remain at zero",
             "note": "Capex and D&A are inputs, not a catalyst unless estimates and price respond."},
            {"id": "k3", "statement": "Implementation risk is not measurable",
             "observable": "Borrow, carry, crowding, options and hedge ledger",
             "threshold": "Any required field missing", "check_date": "before entry",
             "action": "remain at zero",
             "note": "A short cannot be sized from public valuation arithmetic alone."},
        ],
        "catalysts": [
            {"date": "late October 2026 window", "confirmed": False,
             "event": "Q3 FY2026 results; exact date not announced",
             "learn": "D&A/revenue, EBITDA offset and capex trajectory", "tests": "k1"},
            {"date": "after the next filing", "confirmed": False,
             "event": "Consensus revision window",
             "learn": "Whether canonical FY2027 EPS estimates move below the current vendor snapshot",
             "tests": "k2"},
            {"date": "before any entry", "confirmed": False,
             "event": "Implementation review",
             "learn": "Borrow, carry, crowding, options and hedge economics", "tests": "k3"},
        ],
        "falsification": [
            "The strongest case against a short is operating leverage: AI infrastructure may expand "
            "revenue and EBITDA quickly enough that rising D&A never produces a negative EPS revision.",
            "The available FY2027 consensus snapshot is not broker-level and conflicts with the "
            "model range. Treating it as a verified Street target would create false precision.",
            "The DCF cross-check is dominated by terminal value and discount-rate assumptions, so it "
            "is a risk frame rather than the selected causal stock thesis.",
            "The upside case is not capped. Without current borrow, crowding, options and hedge data, "
            "a probabilistic short recommendation is not implementable.",
        ],
        "pre_mortem": (
            "We shorted before proof and lost money because revenue and EBITDA scaled faster than D&A, "
            "consensus EPS revised up, the stock rerated, and crowded borrow made the loss worse. The "
            "preventive action is the current one: wait, require the causal evidence, and keep size at zero."),
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
             "It is priced. Our base case is 12% below spot, our revenue path is inside the analyst "
             "range every year, and we hold no variant view. Nearly half of fiscal 2027 is "
             "already reported or guided, which leaves less to disagree about than usual."},
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
            {"date": "2026-08-26", "confirmed": True, "event": "Q2 FY2027 results",
             "learn": ("Whether the $91.0bn +/- 2% guide holds, Rubin ramp pricing, networking "
                       "attach, and whether any China Data Center compute revenue returns -- the "
                       "guide assumes none, so it is upside management has explicitly excluded"),
             "tests": "k2"},
            {"date": "2026-11-18", "confirmed": False, "event": "Q3 FY2027 results",
             "learn": "Inventory and purchase commitments against the forward guide", "tests": "k3"},
            {"date": "2027-02-25", "confirmed": False, "event": "Q4 FY2027 results and Form 10-K",
             "learn": "Customer concentration and the full equity-stake disclosure", "tests": "k1"},
        ],
        "falsification": [
            "The case for owning it anyway: on an EV/NOPAT basis for a business growing revenue "
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
    """Compatibility view with no capital recommendation.

    Scenario arithmetic is retained for legacy report surfaces, but size is
    zero until a real implementation ledger and portfolio constraints are
    supplied.
    """
    ev = expected_value(scen, probs)
    if direction == "SHORT":
        reward, risk = spot - ev, max(scen["bull"] - spot, 1e-9)
    else:
        reward, risk = ev - spot, max(spot - scen["bear"], 1e-9)
    b = reward / risk if risk else 0.0
    return {
        "expected_value": ev, "reward": reward, "risk": risk, "b": b,
        "position_size": 0.0,
        "binding_constraint": "implementation evidence missing", "risk_reward": b,
        "nav_basis": "no capital recommendation; implementation inputs missing",
    }
