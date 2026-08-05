"""Quality-of-earnings pass. Establishes a clean base year before any modelling."""
import sec

BS = [
    ("Cash & equivalents", "CashAndCashEquivalentsAtCarryingValue"),
    ("Marketable securities (ST)", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"),
    ("Marketable securities (LT)", "AvailableForSaleSecuritiesDebtSecuritiesNoncurrent"),
    ("Non-marketable equity secs", "EquitySecuritiesWithoutReadilyDeterminableFairValueAmount"),
    ("Equity method investments", "EquityMethodInvestments"),
    ("Total assets", "Assets"),
    ("LT debt (noncurrent)", "LongTermDebtNoncurrent"),
    ("LT debt (current)", "LongTermDebtCurrent"),
    ("Operating lease liab (NC)", "OperatingLeaseLiabilityNoncurrent"),
    ("Operating lease liab (C)", "OperatingLeaseLiabilityCurrent"),
    ("Accounts receivable", "AccountsReceivableNetCurrent"),
    ("Inventory", "InventoryNet"),
    ("Accounts payable", "AccountsPayableCurrent"),
    ("Accrued liabilities", "AccruedLiabilitiesCurrent"),
    ("Deferred revenue (current)", "ContractWithCustomerLiabilityCurrent"),
    ("PP&E net", "PropertyPlantAndEquipmentNet"),
]

IS = [
    ("Revenue", "Revenues"),
    ("Revenue (ASC606 tag)", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    ("Cost of revenue", "CostOfRevenue"),
    ("R&D", "ResearchAndDevelopmentExpense"),
    ("Operating income", "OperatingIncomeLoss"),
    ("Non-operating income", "NonoperatingIncomeExpense"),
    ("  of which equity-sec gains", "EquitySecuritiesFvNiGainLoss"),
    ("  of which unrealized", "EquitySecuritiesFvNiUnrealizedGainLoss"),
    ("Pretax income", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"),
    ("Tax expense", "IncomeTaxExpenseBenefit"),
    ("Net income", "NetIncomeLoss"),
    ("Diluted EPS", "EarningsPerShareDiluted"),
]

CF = [
    ("Cash from operations", "NetCashProvidedByUsedInOperatingActivities"),
    ("Capex", "PaymentsToAcquirePropertyPlantAndEquipment"),
    ("D&A", "DepreciationDepletionAndAmortization"),
    ("Depreciation only", "Depreciation"),
    ("Stock-based comp", "ShareBasedCompensation"),
    ("Buybacks", "PaymentsForRepurchaseOfCommonStock"),
]

SHARES = [
    ("Diluted WASO", "WeightedAverageNumberOfDilutedSharesOutstanding"),
    ("Basic WASO", "WeightedAverageNumberOfSharesOutstandingBasic"),
]


def show(ticker, title, tags, kind, n=6, scale=1e9, dp=1):
    print(f"\n=== {ticker} :: {title} ({'$bn' if scale == 1e9 else 'units'}) ===")
    fn = {"q": sec.quarterly, "a": sec.annual, "i": sec.instant}[kind]
    data = {}
    for label, tag in tags:
        unit = "USD/shares" if "EPS" in label else ("shares" if "WASO" in label else None)
        data[label] = fn(ticker, tag, unit=unit)
    ends = sorted(set().union(*[set(d) for d in data.values() if d]))[-n:]
    print("%-30s" % "", " ".join("%10s" % e for e in ends))
    for label, _ in tags:
        d = data[label]
        if not d:
            print("%-30s" % label[:30], "   -- not reported --")
            continue
        row = []
        for e in ends:
            row.append("%10s" % (f"{d[e]['val'] / scale:,.{dp}f}" if e in d else "."))
        print("%-30s" % label[:30], " ".join(row))
    return data


if __name__ == "__main__":
    for t in ("GOOGL", "NVDA"):
        show(t, "Income statement (quarterly)", IS, "q")
        show(t, "Cash flow (quarterly)", CF, "q")
        show(t, "Balance sheet (instant)", BS, "i")
        show(t, "Share count (quarterly)", SHARES, "q", scale=1e6, dp=0)
