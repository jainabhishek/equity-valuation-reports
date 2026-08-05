"""Independent verification: recalculate the workbook and compare it to the Python model.

This is the check that matters. The workbook and the Python engine are two
separate implementations of the same model; if they disagree, one of them is
wrong and the published number cannot be trusted. Comparing Python to itself
would prove nothing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import formulas

DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent.parent
TOL = 0.01  # cents per share


def solve(path):
    xl = formulas.ExcelModel().loads(str(path)).finish()
    return xl.calculate()


def find(sol, sheet, cell, book):
    key = f"'[{book}]{sheet.upper()}'!{cell.upper()}"
    for k, v in sol.items():
        if k.upper().endswith(f"]{sheet.upper()}'!{cell.upper()}"):
            try:
                return float(v.value[0, 0])
            except Exception:
                try:
                    return float(v.value)
                except Exception:
                    return None
    return None


def label_row(path, sheet, label):
    from openpyxl import load_workbook
    ws = load_workbook(path)[sheet]
    for row in ws.iter_rows(min_col=1, max_col=1):
        if row[0].value == label:
            return row[0].row
    return None


def main():
    res = json.loads((DATA / "results.json").read_text())
    failures, checks = [], 0

    for ticker, slug in (("GOOGL", "alphabet"), ("NVDA", "nvidia")):
        path = OUT / slug / "model.xlsx"
        book = path.name
        print(f"\n{'=' * 66}\n{ticker}: recalculating {path.name}\n{'=' * 66}")
        sol = solve(path)

        expected = {
            "Value per share": res[ticker]["scenarios"]["base"]["value_per_share"],
            "Enterprise value": res[ticker]["scenarios"]["base"]["enterprise_value"],
            "Equity value": res[ticker]["scenarios"]["base"]["equity_value"],
            "Terminal value % of EV": res[ticker]["scenarios"]["base"]["tv_pct_ev"],
        }
        for label, exp in expected.items():
            r = label_row(path, "Valuation", label)
            got = find(sol, "Valuation", f"B{r}", book)
            checks += 1
            if got is None:
                failures.append(f"{ticker} {label}: workbook produced no value")
                print(f"  {label:<26} MISSING")
                continue
            tol = TOL if "share" in label else max(abs(exp) * 1e-6, 1e-6)
            ok = abs(got - exp) <= tol
            if not ok:
                failures.append(f"{ticker} {label}: workbook {got:,.6f} vs python {exp:,.6f}")
            flag = "ok" if ok else "MISMATCH"
            if abs(exp) > 1000:
                print(f"  {label:<26} workbook {got / 1e9:>12,.3f}bn   python {exp / 1e9:>12,.3f}bn   {flag}")
            else:
                print(f"  {label:<26} workbook {got:>12,.4f}     python {exp:>12,.4f}     {flag}")

        # every forecast-year FCFF must tie as well, not just the headline
        r = label_row(path, "Valuation", "FCFF")
        for i in range(6):
            col = chr(ord("B") + i)
            got = find(sol, "Valuation", f"{col}{r}", book)
            exp = res[ticker]["scenarios"]["base"]["rows"][i]["fcff"]
            checks += 1
            if got is None or abs(got - exp) > max(abs(exp) * 1e-6, 1.0):
                failures.append(f"{ticker} FCFF year {i + 1}: workbook {got} vs python {exp:,.2f}")
        print(f"  {'FCFF, all 6 years':<26} {'ok' if not any('FCFF' in f for f in failures) else 'MISMATCH'}")

    print(f"\n{'=' * 66}")
    if failures:
        print(f"FAILED — {len(failures)} of {checks} checks did not tie:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"PASSED — all {checks} checks tie between the workbook and the Python model.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
