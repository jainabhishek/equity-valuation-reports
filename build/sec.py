"""Minimal SEC XBRL client. Facts come from the filings, not from memory."""
import json, os, time, urllib.request
from datetime import date
from pathlib import Path

# SEC asks automated clients to identify a contact.  Keep research traffic on
# the approved business channel; never fall back to a personal mailbox.
UA = "Abhishek Jain hello@luckbhi.com"
CACHE = Path(__file__).parent / "data" / "sec"
CACHE.mkdir(parents=True, exist_ok=True)

CIK = {"GOOGL": "0001652044", "NVDA": "0001045810"}


def _get(url: str, cache_key: str) -> dict:
    f = CACHE / f"{cache_key}.json"
    if f.exists():
        return json.loads(f.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            raw = urllib.request.urlopen(req, timeout=60).read()
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    f.write_bytes(raw)
    time.sleep(0.15)  # SEC fair-access
    return json.loads(raw)


def concept(ticker: str, tag: str, taxonomy: str = "us-gaap") -> dict | None:
    """Raw companyconcept payload, or None if the tag isn't reported."""
    cik = CIK[ticker]
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json"
    try:
        return _get(url, f"{ticker}_{taxonomy}_{tag}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _rows(payload: dict, unit: str | None = None) -> list[dict]:
    units = payload["units"]
    key = unit or next(iter(units))
    return units[key]


def quarterly(ticker: str, tag: str, taxonomy: str = "us-gaap", unit: str | None = None):
    """Duration facts spanning ~one quarter, deduped to the latest filing per period end."""
    p = concept(ticker, tag, taxonomy)
    if p is None:
        return {}
    out = {}
    for u in _rows(p, unit):
        if not u.get("start") or not u.get("end"):
            continue
        s, e = date.fromisoformat(u["start"]), date.fromisoformat(u["end"])
        if not (80 <= (e - s).days <= 100):
            continue
        prev = out.get(u["end"])
        # prefer the most recently filed value for a given period end
        if prev is None or u["filed"] >= prev["filed"]:
            out[u["end"]] = {"val": u["val"], "form": u["form"], "accn": u["accn"], "filed": u["filed"]}
    return dict(sorted(out.items()))


def annual(ticker: str, tag: str, taxonomy: str = "us-gaap", unit: str | None = None):
    """Duration facts spanning ~one year."""
    p = concept(ticker, tag, taxonomy)
    if p is None:
        return {}
    out = {}
    for u in _rows(p, unit):
        if not u.get("start") or not u.get("end"):
            continue
        s, e = date.fromisoformat(u["start"]), date.fromisoformat(u["end"])
        if not (350 <= (e - s).days <= 380):
            continue
        prev = out.get(u["end"])
        if prev is None or u["filed"] >= prev["filed"]:
            out[u["end"]] = {"val": u["val"], "form": u["form"], "accn": u["accn"], "filed": u["filed"]}
    return dict(sorted(out.items()))


def instant(ticker: str, tag: str, taxonomy: str = "us-gaap", unit: str | None = None):
    """Point-in-time facts (balance sheet)."""
    p = concept(ticker, tag, taxonomy)
    if p is None:
        return {}
    out = {}
    for u in _rows(p, unit):
        if u.get("start"):
            continue
        prev = out.get(u["end"])
        if prev is None or u["filed"] >= prev["filed"]:
            out[u["end"]] = {"val": u["val"], "form": u["form"], "accn": u["accn"], "filed": u["filed"]}
    return dict(sorted(out.items()))


def fmt(n, scale=1e9, dp=1):
    return "n/a" if n is None else f"{n / scale:,.{dp}f}"
