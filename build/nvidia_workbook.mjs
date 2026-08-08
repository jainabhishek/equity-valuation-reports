/** Build the PM-ready Nvidia workbook with @oai/artifact-tool. */
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const moduleCandidates = [
  process.env.ARTIFACT_TOOL_MODULE,
  path.join(repoRoot, "node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"),
  path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"),
].filter(Boolean);
let moduleFile;
for (const candidate of moduleCandidates) {
  try {
    await fs.access(candidate);
    moduleFile = candidate;
    break;
  } catch {
    // Try the next supported installation location.
  }
}
if (!moduleFile) {
  throw new Error("@oai/artifact-tool not found; set ARTIFACT_TOOL_MODULE to artifact_tool.mjs");
}
const { Workbook, SpreadsheetFile } = await import(pathToFileURL(moduleFile).href);
const data = JSON.parse(await fs.readFile(path.join(repoRoot, "build/data/nvidia_pm.json"), "utf8"));

const COLORS = {
  navy: "#163A5F",
  teal: "#0B6B68",
  red: "#A63D40",
  ink: "#151923",
  muted: "#626B78",
  line: "#D9E0E6",
  soft: "#EEF2F5",
  paleTeal: "#EAF4F3",
  paleRed: "#F6ECEC",
  white: "#FFFFFF",
};
const fmt = {
  currency: "$#,##0.00;[Red]($#,##0.00);-",
  bn: "$#,##0.0;[Red]($#,##0.0);-",
  pct: "0.0%;[Red](0.0%);-",
  pct2: "0.00%;[Red](0.00%);-",
  multiple: "0.00x",
  integer: "0",
};

const workbook = Workbook.create();
const names = [
  "Cover", "Review", "Sources", "Drivers", "WACC", "Revenue", "Depreciation",
  "Equity Bridge", "Valuation", "Scenarios", "Reverse DCF", "Sensitivities",
  "Decision", "Checks", "Notes",
];
const sheets = Object.fromEntries(names.map((name) => [name, workbook.worksheets.add(name)]));
for (const sheet of Object.values(sheets)) {
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(3);
}

function title(sheet, text, subtitle, endCol = "H") {
  const band = sheet.getRange(`A1:${endCol}1`);
  band.merge();
  band.values = [[text]];
  band.format.fill = COLORS.navy;
  band.format.font = { bold: true, color: COLORS.white, size: 18 };
  band.format.rowHeight = 30;
  const sub = sheet.getRange(`A2:${endCol}2`);
  sub.merge();
  sub.values = [[subtitle]];
  sub.format.fill = COLORS.soft;
  sub.format.font = { color: COLORS.muted, italic: true, size: 10 };
  sub.format.wrapText = true;
  sub.format.rowHeight = 28;
}

function section(sheet, range, text) {
  const r = sheet.getRange(range);
  r.merge();
  r.values = [[text]];
  r.format.fill = COLORS.navy;
  r.format.font = { bold: true, color: COLORS.white, size: 10 };
}

function header(sheet, range) {
  const r = sheet.getRange(range);
  r.format.fill = COLORS.soft;
  r.format.font = { bold: true, color: COLORS.ink, size: 9 };
  r.format.borders = { preset: "all", style: "thin", color: COLORS.line };
  r.format.wrapText = true;
}

function box(sheet, range) {
  const r = sheet.getRange(range);
  r.format.borders = { preset: "all", style: "thin", color: COLORS.line };
}

function styleInputs(sheet, range) {
  const r = sheet.getRange(range);
  r.format.font = { color: "#1F5F99" };
  r.format.fill = "#F3F7FA";
}

function setWidths(sheet, widths) {
  for (const [col, width] of Object.entries(widths)) sheet.getRange(`${col}:${col}`).format.columnWidth = width;
}

function formulaValueAt(waccCell, growthCell) {
  const fcffRow = 42;
  const periodRow = 43;
  const terms = ["B", "C", "D", "E", "F", "G"]
    .map((col) => `Valuation!${col}${fcffRow}/(1+${waccCell})^Valuation!${col}${periodRow}`)
    .join("+");
  return `=(${terms}+Valuation!G36*(1-${growthCell}/Scenarios!$D$27)*(1+${growthCell})/(${waccCell}-${growthCell})/(1+${waccCell})^Drivers!$B$32+'Equity Bridge'!$C$15)/Drivers!$B$6`;
}

// ---------------------------------------------------------------------------
// Cover
// ---------------------------------------------------------------------------
{
  const s = sheets.Cover;
  title(s, "NVIDIA | PM review model", `Public-information risk frame | Market cut ${data.meta.as_of} | Share-ready, not capital-ready`, "J");
  s.getRange("A4:J4").merge();
  s.getRange("A4:J4").values = [["WATCHLIST / NO POSITION"]];
  s.getRange("A4:J4").format.fill = COLORS.teal;
  s.getRange("A4:J4").format.font = { bold: true, color: COLORS.white, size: 20 };
  s.getRange("A4:J4").format.rowHeight = 34;
  s.getRange("A6:B10").values = [
    ["Spot", null],
    ["Bear value", null],
    ["Base value", null],
    ["Bull value", null],
    ["Position size", null],
  ];
  s.getRange("B6:B10").formulas = [["=Decision!B5"], ["=Decision!B6"], ["=Decision!B7"], ["=Decision!B8"], ["=Decision!B13"]];
  s.getRange("B6:B9").format.numberFormat = fmt.currency;
  s.getRange("B10").format.numberFormat = "0.0%";
  box(s, "A6:B10");
  s.getRange("D6:J6").merge(); s.getRange("D6:J6").values = [["PM call"]];
  s.getRange("D6:J6").format.fill = COLORS.soft; s.getRange("D6:J6").format.font = { bold: true, color: COLORS.navy };
  s.getRange("D7:J10").merge();
  s.getRange("D7:J10").values = [["Do not force a trade. The business is exceptional, but no verified near-term variant exists. The base DCF is below spot, the bull state is uncapped, and every capital gate remains open."]];
  s.getRange("D7:J10").format.wrapText = true; s.getRange("D7:J10").format.font = { size: 12, color: COLORS.ink };
  s.getRange("D7:J10").format.fill = COLORS.paleTeal; box(s, "D6:J10");
  section(s, "A13:J13", "Workbook map");
  s.getRange("A14:J21").values = [
    ["Review", "Eight highest-priority defects and their resolutions", "Sources", "Source ledger with URL and use", "Drivers", "Filed facts and analyst inputs", "WACC", "Explicit CAPM build", "Revenue", "Q1/Q2/FY27 bridge"],
    ["Depreciation", "Opening D&A plus forecast vintages", "Equity Bridge", "Haircuts by asset type", "Valuation", "Three formula-driven DCFs", "Scenarios", "Unweighted state summary", "Reverse DCF", "Spot-implied assumptions"],
    ["Sensitivities", "WACC × terminal growth", "Decision", "Action rules and capital gates", "Checks", "Formula controls", "Notes", "Conventions and limitations", "", ""],
    ["", "", "", "", "", "", "", "", "", ""],
    ["Status", "All calculation checks must pass", "", "", "", "", "", "", "", ""],
    ["Check failures", null, "", "", "", "", "", "", "", ""],
    ["Capital gates open", null, "", "", "", "", "", "", "", ""],
    ["Workbook purpose", "Audit the risk frame; do not use it as an executable order ticket.", "", "", "", "", "", "", "", ""],
  ];
  s.getRange("B19").formulas = [["=Checks!B15"]];
  s.getRange("B20").formulas = [["=Decision!B12"]];
  s.getRange("B19:B20").format.numberFormat = fmt.integer;
  s.getRange("A14:J21").format.wrapText = true; box(s, "A14:J21");
  setWidths(s, { A: 17, B: 25, C: 17, D: 25, E: 17, F: 25, G: 17, H: 25, I: 17, J: 25 });
}

// ---------------------------------------------------------------------------
// Review
// ---------------------------------------------------------------------------
{
  const s = sheets.Review;
  title(s, "Review remediation log", "Every highest-priority finding is fixed in the memo and model; unresolved evidence sits in Decision as an open capital gate.", "D");
  s.getRange("A4:D4").values = [["Priority finding", "Status", "Resolution", "PM impact"]]; header(s, "A4:D4");
  const impacts = [
    "Prevents contradictory meeting materials.", "Corrects operating quality and earnings attribution.",
    "Raises FY2027 D&A to a defensible formula-driven run-rate.", "Removes false precision from retired segment categories.",
    "Makes duration and discount-rate risk explicit.", "Prevents excess terminal cash conversion.",
    "Stops cash-equivalent treatment of risky strategic assets.", "Prevents unsupported expected value and sizing.",
  ];
  s.getRange("A5:D12").values = data.review_findings.map((row, i) => [...row, impacts[i]]);
  s.getRange("B5:B12").format.fill = COLORS.paleTeal; s.getRange("B5:B12").format.font = { bold: true, color: COLORS.teal };
  s.getRange("A5:D12").format.wrapText = true; box(s, "A5:D12");
  setWidths(s, { A: 38, B: 12, C: 54, D: 48 });
}

// ---------------------------------------------------------------------------
// Sources
// ---------------------------------------------------------------------------
{
  const s = sheets.Sources;
  title(s, "Source ledger", "Hardcoded facts cite a source ID at point of use. Analyst assumptions are labeled S7; market data must be refreshed before risk.", "F");
  s.getRange("A4:F4").values = [["ID", "Type", "Date", "Source", "Use", "URL"]]; header(s, "A4:F4");
  s.getRange(`A5:F${4 + data.sources.length}`).values = data.sources.map((x) => [x.id, x.type, x.date, x.title, x.use, x.url]);
  s.getRange(`A5:F${4 + data.sources.length}`).format.wrapText = true; box(s, `A5:F${4 + data.sources.length}`);
  setWidths(s, { A: 8, B: 20, C: 13, D: 34, E: 60, F: 72 });
}

// ---------------------------------------------------------------------------
// Drivers
// ---------------------------------------------------------------------------
{
  const s = sheets.Drivers;
  title(s, "Drivers and filed facts", "Blue cells are hardcoded inputs. Every fact has a source ID; S7 marks analyst assumptions.", "D");
  s.getRange("A4:D4").values = [["Input", "Value", "Source", "Use / caveat"]]; header(s, "A4:D4");
  const rows = [
    ["Spot", data.market.spot, "S5", "Frozen regular-hours reference; not executable"],
    ["Diluted shares, bn", data.market.shares_bn, "S1", "Q1 FY2027 weighted average"],
    ["FY2026 revenue, $bn", data.facts.fy2026_revenue, "S3", "Historical anchor"],
    ["Q1 FY2027 revenue, $bn", data.facts.q1_revenue, "S1/S2", "Reported"],
    ["Q2 guide midpoint, $bn", data.facts.q2_guide, "S2", "±2%; no China DC compute"],
    ["Q1 CFO, $bn", 50.344, "S1", "Reported"],
    ["Q1 capex, $bn", 1.757, "S1", "Reported productive assets"],
    ["Q1 FCF proxy, $bn", null, "Calc", "CFO less capex; used only to remove Q1 from FY27 DCF"],
    ["Opening TTM D&A, $bn", 3.229, "S1", "Opening run-rate block"],
    ["Q1 D&A, $bn", 0.997, "S1", "Reported"],
    ["Remaining FY2027 intangible amort., $bn", 0.689, "S1", "Disclosed future amortization"],
    ["", null, "", ""],
    ["Liquid cash + marketable debt, $bn", data.balance_sheet.liquid_cash_and_debt_securities, "S1/S2", "Cash 13.237 + marketable debt 37.098"],
    ["Marketable equity, $bn", data.balance_sheet.marketable_equity, "S1", "$27.4bn subject to short-term lock-ups"],
    ["Nonmarketable equity, $bn", data.balance_sheet.nonmarketable_equity, "S1", "Illiquid carrying value"],
    ["Equity-method stakes, $bn", data.balance_sheet.equity_method, "S1", "Infrastructure funds"],
    ["Debt, $bn", data.balance_sheet.debt, "S1", "Current + long-term notes"],
    ["Operating leases, $bn", data.balance_sheet.operating_leases_disclosed_not_deducted, "S1", "Disclosed, not deducted; lease expense is in operations"],
    ["", null, "", ""],
    ["Risk-free rate", data.wacc.risk_free_rate, "S4", "Aug. 7 ten-year Treasury"],
    ["Normalized beta", data.wacc.beta, "S7", "Analyst assumption"],
    ["Equity risk premium", data.wacc.equity_risk_premium, "S7", "Analyst assumption"],
    ["Pre-tax debt cost", data.wacc.pre_tax_debt_cost, "S7", "Analyst assumption"],
    ["Marginal tax rate", data.wacc.tax_rate, "S7", "Analyst assumption"],
    ["", null, "", ""],
    ["Required net return", data.decision.required_return, "S7", "Minimum observable-variant hurdle"],
    ["First stub period, years", 0.24, "S7", "Aug. 8 to midpoint of remaining FY2027 cash flows"],
    ["Terminal period, years", 5.47, "S7", "Aug. 8 to FY2032 year-end"],
    ["Short-lived asset share", 0.60, "S7", "Depreciation assumption"],
    ["Short useful life, years", 5.0, "S7", "Depreciation assumption"],
    ["Long useful life, years", 20.0, "S7", "Depreciation assumption"],
    ["", null, "", ""],
    ["Q1 equity-security gains, $bn", data.facts.q1_equity_security_gains, "S1", "Do not treat as operating earnings"],
    ["Q1 pretax income, $bn", data.facts.q1_pretax_income, "S1", "Reported"],
    ["Q1 inventory, $bn", data.facts.q1_inventory, "S1", "Read with guide and cancellations"],
    ["Manufacturing commitments, $bn", data.facts.manufacturing_commitments, "S1", "95bn payable in remaining FY2027"],
    ["Cloud commitments, $bn", data.facts.cloud_commitments, "S1", "Multi-year R&D capacity"],
    ["Investment commitments, $bn", data.facts.investment_commitments, "S1", "Contingent; expected in remaining FY2027"],
  ];
  s.getRange(`A5:D${4 + rows.length}`).values = rows;
  s.getRange("B12").formulas = [["=B10-B11"]];
  styleInputs(s, `B5:B${4 + rows.length}`); s.getRange("B12").format.fill = COLORS.paleTeal; s.getRange("B12").format.font = { color: COLORS.teal };
  s.getRange("B5:B23").format.numberFormat = fmt.bn;
  s.getRange("B24:B28").format.numberFormat = fmt.pct;
  s.getRange("B25").format.numberFormat = fmt.multiple;
  s.getRange("B30:B30").format.numberFormat = fmt.pct;
  s.getRange("B31:B35").format.numberFormat = "0.00";
  s.getRange("B37:B42").format.numberFormat = fmt.bn;
  s.getRange(`A5:D${4 + rows.length}`).format.wrapText = true; box(s, `A5:D${4 + rows.length}`);
  setWidths(s, { A: 43, B: 18, C: 13, D: 66 });
}

// ---------------------------------------------------------------------------
// WACC
// ---------------------------------------------------------------------------
{
  const s = sheets.WACC;
  title(s, "WACC build", "CAPM is explicit. The base scenario uses the rounded output; bear and bull add visible spreads.", "D");
  s.getRange("A4:D4").values = [["Component", "Value", "Formula / source", "Comment"]]; header(s, "A4:D4");
  s.getRange("A5:D16").values = [
    ["Risk-free rate", null, "S4", "Ten-year Treasury"], ["Beta", null, "S7", "Normalized analyst assumption"],
    ["Equity risk premium", null, "S7", "Analyst assumption"], ["Cost of equity", null, "Rf + beta × ERP", "CAPM"],
    ["Market capitalization, $bn", null, "Spot × diluted shares", "Market-value weight"], ["Debt, $bn", null, "S1", "Current + long-term"],
    ["Equity weight", null, "Market value / capital", ""], ["Debt weight", null, "Debt / capital", ""],
    ["After-tax debt cost", null, "Kd × (1 − tax)", ""], ["Calculated WACC", null, "Weighted cost", ""],
    ["Base model WACC", null, "Rounded calculated WACC", "Used by base scenario"], ["Rounding difference", null, "Model less calculated", "Control"],
  ];
  s.getRange("B5:B16").formulas = [
    ["=Drivers!B24"], ["=Drivers!B25"], ["=Drivers!B26"], ["=B5+B6*B7"],
    ["=Drivers!B5*Drivers!B6"], ["=Drivers!B21"], ["=B9/(B9+B10)"], ["=B10/(B9+B10)"],
    ["=Drivers!B27*(1-Drivers!B28)"], ["=B11*B8+B12*B13"], ["=ROUND(B14,3)"], ["=B15-B14"],
  ];
  s.getRange("B5:B8").format.numberFormat = fmt.pct2; s.getRange("B6").format.numberFormat = fmt.multiple; s.getRange("B9:B10").format.numberFormat = fmt.bn;
  s.getRange("B11:B16").format.numberFormat = fmt.pct2;
  s.getRange("B14:B15").format.fill = COLORS.paleTeal; s.getRange("B14:B15").format.font = { bold: true, color: COLORS.teal };
  s.getRange("A5:D16").format.wrapText = true; box(s, "A5:D16"); setWidths(s, { A: 34, B: 18, C: 28, D: 42 });
}

// ---------------------------------------------------------------------------
// Scenarios (inputs first, output summary links back from Valuation)
// ---------------------------------------------------------------------------
{
  const s = sheets.Scenarios;
  title(s, "Scenario assumptions", "Three states, no probabilities. Revenue is consolidated because Nvidia retired the prior product-market framework.", "I");
  s.getRange("A3:G3").values = [["Fiscal year", ...data.scenarios.base.rows.map((r) => r.year)]]; header(s, "A3:G3");
  const starts = { bear: 4, base: 11, bull: 18 };
  for (const [key, start] of Object.entries(starts)) {
    const c = data.scenarios[key];
    s.getRange(`A${start}:G${start}`).merge(); s.getRange(`A${start}:G${start}`).values = [[c.label]];
    s.getRange(`A${start}:G${start}`).format.fill = key === "base" ? COLORS.teal : COLORS.navy;
    s.getRange(`A${start}:G${start}`).format.font = { bold: true, color: COLORS.white };
    s.getRange(`A${start + 1}:G${start + 5}`).values = [
      ["Revenue, $bn", ...c.rows.map((r) => r.revenue)],
      ["EBITDA margin", ...c.rows.map((r) => r.ebitda_margin)],
      ["Capex / revenue", ...c.rows.map((r) => r.capex_pct)],
      ["Tax rate", ...c.rows.map((r) => r.tax_rate)],
      ["NWC / revenue", ...c.rows.map((r) => r.nwc_pct)],
    ];
    styleInputs(s, `B${start + 1}:G${start + 5}`);
    s.getRange(`B${start + 1}:G${start + 1}`).format.numberFormat = fmt.bn;
    s.getRange(`B${start + 2}:G${start + 5}`).format.numberFormat = fmt.pct;
    box(s, `A${start + 1}:G${start + 5}`);
  }
  s.getRange("A25:I25").values = [["State", "WACC", "g", "Terminal ROIC", "Public equity credit", "Private equity credit", "Equity-method credit", "DCF / share", "Vs spot"]]; header(s, "A25:I25");
  s.getRange("A26:G28").values = [
    ["Bear", null, data.scenarios.bear.terminal_growth, data.scenarios.bear.terminal_roic, data.scenarios.bear.bridge.marketable_credit, data.scenarios.bear.bridge.nonmarketable_credit, data.scenarios.bear.bridge.equity_method_credit],
    ["Base", null, data.scenarios.base.terminal_growth, data.scenarios.base.terminal_roic, data.scenarios.base.bridge.marketable_credit, data.scenarios.base.bridge.nonmarketable_credit, data.scenarios.base.bridge.equity_method_credit],
    ["Bull", null, data.scenarios.bull.terminal_growth, data.scenarios.bull.terminal_roic, data.scenarios.bull.bridge.marketable_credit, data.scenarios.bull.bridge.nonmarketable_credit, data.scenarios.bull.bridge.equity_method_credit],
  ];
  s.getRange("B26:B28").formulas = [["=WACC!B15+1.25%"], ["=WACC!B15"], ["=WACC!B15-0.75%"]];
  s.getRange("H26:I28").formulas = [["=Valuation!J18", "=H26/Drivers!B5-1"], ["=Valuation!J41", "=H27/Drivers!B5-1"], ["=Valuation!J64", "=H28/Drivers!B5-1"]];
  s.getRange("B26:G28").format.numberFormat = fmt.pct; s.getRange("H26:H28").format.numberFormat = fmt.currency; s.getRange("I26:I28").format.numberFormat = fmt.pct;
  styleInputs(s, "C26:G28"); box(s, "A25:I28"); setWidths(s, { A: 25, B: 14, C: 14, D: 18, E: 20, F: 20, G: 20, H: 16, I: 14 });
}

// ---------------------------------------------------------------------------
// Revenue bridge
// ---------------------------------------------------------------------------
{
  const s = sheets.Revenue;
  title(s, "Revenue anchor and near-term bridge", "Q1 actual plus Q2 guidance replaces the retired product-market build. Street figures are a frozen aggregator reference, not a canonical broker tape.", "D");
  s.getRange("A4:D4").values = [["Item", "Value", "Source", "Interpretation"]]; header(s, "A4:D4");
  s.getRange("A5:D16").values = [
    ["FY2026 revenue, $bn", null, "S3", "Historical base"], ["Q1 FY2027 actual, $bn", null, "S1/S2", "Reported"],
    ["Q2 guide low, $bn", null, "S2", "Midpoint less 2%"], ["Q2 guide midpoint, $bn", null, "S2", "No China DC compute assumed"],
    ["Q2 guide high, $bn", null, "S2", "Midpoint plus 2%"], ["Base FY2027 revenue, $bn", null, "S7", "Analyst scenario"],
    ["H2 required after Q1 + Q2 midpoint, $bn", null, "Calc", "Two quarters"], ["H2 required per quarter, $bn", null, "Calc", "Run-rate"],
    ["Required vs Q2 midpoint", null, "Calc", "Sequential hurdle"], ["Frozen Street FY2027 average, $bn", data.near_term.street_fy2027_avg, "S6", "40-estimate aggregator"],
    ["Frozen Street FY2027 low, $bn", data.near_term.street_fy2027_low, "S6", "Aggregator"], ["Frozen Street FY2027 high, $bn", data.near_term.street_fy2027_high, "S6", "Aggregator"],
  ];
  s.getRange("B5:B13").formulas = [["=Drivers!B7"], ["=Drivers!B8"], ["=Drivers!B9*(1-2%)"], ["=Drivers!B9"], ["=Drivers!B9*(1+2%)"], ["=Scenarios!B12"], ["=B10-B6-B8"], ["=B11/2"], ["=B12/B8-1"]];
  s.getRange("B5:B12").format.numberFormat = fmt.bn; s.getRange("B13").format.numberFormat = fmt.pct; s.getRange("B14:B16").format.numberFormat = fmt.bn;
  s.getRange("B10:B13").format.fill = COLORS.paleTeal; s.getRange("B10:B13").format.font = { bold: true, color: COLORS.teal };
  s.getRange("A5:D16").format.wrapText = true; box(s, "A5:D16");
  section(s, "A19:D19", "Current reporting framework");
  s.getRange("A20:D24").values = [
    ["Q1 total revenue", 81.615, "S1/S2", "Reported"], ["Data Center", 75.246, "S1/S2", "Current market platform"],
    ["Edge Computing", 6.369, "S1/S2", "Current market platform"], ["Prior: Data Center compute", 60.4, "S2", "Prior sub-market, provided for transition"],
    ["Prior: Data Center networking", 14.8, "S2", "Prior sub-market, provided for transition"],
  ];
  s.getRange("B20:B24").format.numberFormat = fmt.bn; box(s, "A20:D24"); setWidths(s, { A: 48, B: 18, C: 15, D: 58 });
}

// ---------------------------------------------------------------------------
// Depreciation
// ---------------------------------------------------------------------------
{
  const s = sheets.Depreciation;
  title(s, "Depreciation schedule", "Opening D&A runs off over five years; forecast capex is depreciated 60% over five years and 40% over twenty years with a half-year convention.", "G");
  s.getRange("A3:G3").values = [["Fiscal year", 2027, 2028, 2029, 2030, 2031, 2032]]; header(s, "A3:G3");
  const starts = { bear: 4, base: 16, bull: 28 };
  const scenarioStarts = { bear: 4, base: 11, bull: 18 };
  for (const [key, start] of Object.entries(starts)) {
    const scStart = scenarioStarts[key];
    s.getRange(`A${start}:G${start}`).merge(); s.getRange(`A${start}:G${start}`).values = [[`${key.toUpperCase()} D&A`]];
    s.getRange(`A${start}:G${start}`).format.fill = key === "base" ? COLORS.teal : COLORS.navy; s.getRange(`A${start}:G${start}`).format.font = { bold: true, color: COLORS.white };
    s.getRange(`A${start + 1}:A${start + 9}`).values = [["Opening D&A runoff"], ["Forecast capex"], ...Array.from({ length: 6 }, (_, i) => [`FY${2027 + i} vintage`]), ["Total D&A"]];
    for (let col = 0; col < 6; col++) {
      const letter = String.fromCharCode(66 + col);
      s.getRange(`${letter}${start + 1}`).formulas = [[`=Drivers!$B$13*MAX(0,1-(${letter}$3-2027)/Drivers!$B$34)`]];
      s.getRange(`${letter}${start + 2}`).formulas = [[`=Scenarios!${letter}${scStart + 1}*Scenarios!${letter}${scStart + 3}`]];
      for (let vintage = 0; vintage < 6; vintage++) {
        const vintageCol = String.fromCharCode(66 + vintage);
        const row = start + 3 + vintage;
        s.getRange(`${letter}${row}`).formulas = [[`=IF(${letter}$3<$A${row},0,${vintageCol}$${start + 2}*(Drivers!$B$33/Drivers!$B$34*IF(${letter}$3-$A${row}=0,0.5,IF(${letter}$3-$A${row}<Drivers!$B$34,1,IF(${letter}$3-$A${row}=Drivers!$B$34,0.5,0)))+(1-Drivers!$B$33)/Drivers!$B$35*IF(${letter}$3-$A${row}=0,0.5,IF(${letter}$3-$A${row}<Drivers!$B$35,1,IF(${letter}$3-$A${row}=Drivers!$B$35,0.5,0)))))`]];
        s.getRange(`A${row}`).values = [[2027 + vintage]];
        s.getRange(`A${row}`).format.numberFormat = '"FY"0';
      }
      s.getRange(`${letter}${start + 9}`).formulas = [[`=SUM(${letter}${start + 1},${letter}${start + 3}:${letter}${start + 8})`]];
    }
    s.getRange(`B${start + 1}:G${start + 9}`).format.numberFormat = fmt.bn; s.getRange(`A${start + 9}:G${start + 9}`).format.fill = COLORS.paleTeal; s.getRange(`A${start + 9}:G${start + 9}`).format.font = { bold: true, color: COLORS.teal };
    box(s, `A${start + 1}:G${start + 9}`);
  }
  setWidths(s, { A: 28, B: 15, C: 15, D: 15, E: 15, F: 15, G: 15 });
}

// ---------------------------------------------------------------------------
// Equity bridge
// ---------------------------------------------------------------------------
{
  const s = sheets["Equity Bridge"];
  title(s, "Equity-value bridge", "Strategic stakes are not cash. Credits vary by scenario; operating leases are disclosed but not deducted because lease expense is already in operating cash flows.", "E");
  s.getRange("A4:E4").values = [["Item", "Bear", "Base", "Bull", "Source / formula"]]; header(s, "A4:E4");
  s.getRange("A5:A15").values = [["Liquid cash + marketable debt"], ["Marketable equity reported"], ["Credit %"], ["Marketable equity credited"], ["Nonmarketable equity reported"], ["Credit %"], ["Nonmarketable equity credited"], ["Equity-method reported"], ["Credit %"], ["Equity-method credited"], ["Total credited bridge (after debt)"]];
  for (let i = 0; i < 3; i++) {
    const col = String.fromCharCode(66 + i);
    const scRow = 26 + i;
    s.getRange(`${col}5:${col}15`).formulas = [
      ["=Drivers!B17"], ["=Drivers!B18"], [`=Scenarios!E${scRow}`], [`=${col}6*${col}7`],
      ["=Drivers!B19"], [`=Scenarios!F${scRow}`], [`=${col}9*${col}10`], ["=Drivers!B20"],
      [`=Scenarios!G${scRow}`], [`=${col}12*${col}13`], [`=SUM(${col}5,${col}8,${col}11,${col}14)-Drivers!B21`],
    ];
  }
  s.getRange("E5:E15").values = [["S1/S2"], ["S1"], ["S7"], ["Calc"], ["S1"], ["S7"], ["Calc"], ["S1"], ["S7"], ["Calc"], ["Calc; debt from S1"]];
  s.getRange("B5:D15").format.numberFormat = fmt.bn; s.getRange("B7:D7").format.numberFormat = fmt.pct; s.getRange("B10:D10").format.numberFormat = fmt.pct; s.getRange("B13:D13").format.numberFormat = fmt.pct;
  s.getRange("A15:D15").format.fill = COLORS.paleTeal; s.getRange("A15:D15").format.font = { bold: true, color: COLORS.teal };
  box(s, "A5:E15"); section(s, "A18:E18", "Disclosed, not in bridge");
  s.getRange("A19:E22").values = [["Operating lease liabilities", data.balance_sheet.operating_leases_disclosed_not_deducted, "", "", "S1; no double deduction"], ["Manufacturing commitments", data.facts.manufacturing_commitments, "", "", "S1; operating/capacity commitments"], ["Cloud commitments", data.facts.cloud_commitments, "", "", "S1; operating/R&D commitments"], ["Investment commitments", data.facts.investment_commitments, "", "", "S1; contingent, open demand-quality gate"]];
  s.getRange("B19:B22").format.numberFormat = fmt.bn; box(s, "A19:E22"); setWidths(s, { A: 38, B: 16, C: 16, D: 16, E: 52 });
}

// ---------------------------------------------------------------------------
// Valuation
// ---------------------------------------------------------------------------
{
  const s = sheets.Valuation;
  title(s, "DCF valuation", "FY2027 removes reported Q1 CFO less capex; terminal FCFF normalizes reinvestment through g / terminal ROIC. Units are $bn except per-share outputs.", "J");
  s.getRange("A3:G3").values = [["Fiscal year", 2027, 2028, 2029, 2030, 2031, 2032]]; header(s, "A3:G3");
  const starts = { bear: 4, base: 27, bull: 50 };
  const scenarioStarts = { bear: 4, base: 11, bull: 18 };
  const daTotals = { bear: 13, base: 25, bull: 37 };
  const scRows = { bear: 26, base: 27, bull: 28 };
  const outputRows = { bear: 18, base: 41, bull: 64 };
  for (const [key, start] of Object.entries(starts)) {
    const scStart = scenarioStarts[key];
    const scRow = scRows[key];
    s.getRange(`A${start}:G${start}`).merge(); s.getRange(`A${start}:G${start}`).values = [[`${key.toUpperCase()} DCF`]];
    s.getRange(`A${start}:G${start}`).format.fill = key === "base" ? COLORS.teal : COLORS.navy; s.getRange(`A${start}:G${start}`).format.font = { bold: true, color: COLORS.white };
    s.getRange(`A${start + 1}:A${start + 18}`).values = [
      ["Revenue"], ["Growth"], ["EBITDA margin"], ["EBITDA"], ["D&A"], ["EBIT"], ["EBIT margin"], ["Tax rate"], ["NOPAT"], ["Capex"], ["NWC / revenue"], ["Change in NWC"], ["Annual FCFF"], ["Less: reported Q1 FCF proxy"], ["DCF FCFF"], ["Discount period"], ["Discount factor"], ["PV of FCFF"],
    ];
    for (let col = 0; col < 6; col++) {
      const letter = String.fromCharCode(66 + col);
      const prev = col === 0 ? "Drivers!$B$7" : `${String.fromCharCode(65 + col)}${start + 1}`;
      const prevNwc = col === 0 ? "11.5%" : `Scenarios!${String.fromCharCode(65 + col)}${scStart + 5}`;
      const formulas = [
        `=Scenarios!${letter}${scStart + 1}`, `=${letter}${start + 1}/${prev}-1`, `=Scenarios!${letter}${scStart + 2}`,
        `=${letter}${start + 1}*${letter}${start + 3}`, `=Depreciation!${letter}${daTotals[key]}`, `=${letter}${start + 4}-${letter}${start + 5}`,
        `=${letter}${start + 6}/${letter}${start + 1}`, `=Scenarios!${letter}${scStart + 4}`, `=${letter}${start + 6}*(1-${letter}${start + 8})`,
        `=Scenarios!${letter}${scStart + 1}*Scenarios!${letter}${scStart + 3}`, `=Scenarios!${letter}${scStart + 5}`,
        `=${letter}${start + 1}*${letter}${start + 11}-${prev}*${prevNwc}`, `=${letter}${start + 9}+${letter}${start + 5}-${letter}${start + 10}-${letter}${start + 12}`,
        col === 0 ? "=Drivers!$B$12" : "=0", `=${letter}${start + 13}-${letter}${start + 14}`,
        `=Drivers!$B$31+${col === 0 ? 0 : col - 0.28}`, `=1/(1+Scenarios!$B$${scRow})^${letter}${start + 16}`, `=${letter}${start + 15}*${letter}${start + 17}`,
      ];
      for (let r = 0; r < formulas.length; r++) s.getRange(`${letter}${start + 1 + r}`).formulas = [[formulas[r]]];
    }
    s.getRange(`B${start + 1}:G${start + 1}`).format.numberFormat = fmt.bn;
    s.getRange(`B${start + 2}:G${start + 3}`).format.numberFormat = fmt.pct;
    s.getRange(`B${start + 4}:G${start + 6}`).format.numberFormat = fmt.bn;
    s.getRange(`B${start + 7}:G${start + 8}`).format.numberFormat = fmt.pct;
    s.getRange(`B${start + 9}:G${start + 10}`).format.numberFormat = fmt.bn;
    s.getRange(`B${start + 11}:G${start + 11}`).format.numberFormat = fmt.pct;
    s.getRange(`B${start + 12}:G${start + 15}`).format.numberFormat = fmt.bn;
    s.getRange(`B${start + 16}:G${start + 16}`).format.numberFormat = "0.00";
    s.getRange(`B${start + 17}:G${start + 17}`).format.numberFormat = "0.000x";
    s.getRange(`B${start + 18}:G${start + 18}`).format.numberFormat = fmt.bn;
    box(s, `A${start + 1}:G${start + 18}`);
    s.getRange(`I${start}:J${start}`).values = [["Summary", "Value"]]; header(s, `I${start}:J${start}`);
    s.getRange(`I${start + 1}:I${start + 15}`).values = [["WACC"], ["Terminal growth"], ["Terminal ROIC"], ["Terminal reinvestment"], ["Terminal FCFF"], ["Terminal value"], ["Terminal period"], ["PV terminal"], ["PV explicit"], ["Enterprise value"], ["Equity bridge"], ["Equity value"], ["Diluted shares, bn"], ["Value per share"], ["Terminal value / EV"]];
    s.getRange(`J${start + 1}:J${start + 15}`).formulas = [
      [`=Scenarios!B${scRow}`], [`=Scenarios!C${scRow}`], [`=Scenarios!D${scRow}`], [`=J${start + 2}/J${start + 3}`],
      [`=G${start + 9}*(1-J${start + 4})`], [`=J${start + 5}*(1+J${start + 2})/(J${start + 1}-J${start + 2})`],
      ["=Drivers!B32"], [`=J${start + 6}/(1+J${start + 1})^J${start + 7}`], [`=SUM(B${start + 18}:G${start + 18})`],
      [`=J${start + 8}+J${start + 9}`], [`='Equity Bridge'!${String.fromCharCode(66 + Object.keys(starts).indexOf(key))}15`],
      [`=J${start + 10}+J${start + 11}`], ["=Drivers!B6"], [`=J${start + 12}/J${start + 13}`], [`=J${start + 8}/J${start + 10}`],
    ];
    s.getRange(`J${start + 1}:J${start + 4}`).format.numberFormat = fmt.pct;
    s.getRange(`J${start + 5}:J${start + 6}`).format.numberFormat = fmt.bn; s.getRange(`J${start + 7}`).format.numberFormat = "0.00";
    s.getRange(`J${start + 8}:J${start + 12}`).format.numberFormat = fmt.bn; s.getRange(`J${start + 13}`).format.numberFormat = "0.000";
    s.getRange(`J${start + 14}`).format.numberFormat = fmt.currency; s.getRange(`J${start + 15}`).format.numberFormat = fmt.pct;
    s.getRange(`I${outputRows[key]}:J${outputRows[key]}`).format.fill = COLORS.paleTeal; s.getRange(`I${outputRows[key]}:J${outputRows[key]}`).format.font = { bold: true, color: COLORS.teal };
    box(s, `I${start}:J${start + 15}`);
  }
  setWidths(s, { A: 30, B: 14, C: 14, D: 14, E: 14, F: 14, G: 14, H: 3, I: 28, J: 18 });
}

// ---------------------------------------------------------------------------
// Scenario output note
// ---------------------------------------------------------------------------
{
  const s = sheets.Scenarios;
  s.getRange("A31:I31").merge(); s.getRange("A31:I31").values = [["Decision use"]]; s.getRange("A31:I31").format.fill = COLORS.navy; s.getRange("A31:I31").format.font = { bold: true, color: COLORS.white };
  s.getRange("A32:I35").merge(); s.getRange("A32:I35").values = [["These are state-contingent risk frames, not a probability distribution. The workbook does not calculate expected value or Kelly sizing. A non-zero position requires an observable variant, a live market/implementation ledger and at least 20% net underwritten return."]]; s.getRange("A32:I35").format.wrapText = true; s.getRange("A32:I35").format.fill = COLORS.paleTeal; box(s, "A32:I35");
}

// ---------------------------------------------------------------------------
// Reverse DCF
// ---------------------------------------------------------------------------
{
  const s = sheets["Reverse DCF"];
  title(s, "Reverse DCF", "Two non-equivalent diagnostics: the WACC that closes the gap on the base operating path, or a uniform revenue scale at the explicit CAPM rate.", "D");
  s.getRange("A4:D4").values = [["Diagnostic", "Value", "Control", "Interpretation"]]; header(s, "A4:D4");
  s.getRange("A5:D15").values = [
    ["Spot", null, "S5", "Frozen reference"], ["Spot-implied WACC", data.reverse.implied_wacc, "Python bisection", "Holds base operations, g, ROIC and bridge constant"],
    ["Model value at implied WACC", null, "Formula", "Should equal spot"], ["Residual", null, "Formula", "Should be approximately zero"],
    ["Base WACC", null, "WACC build", "Rounded CAPM output"], ["WACC gap", null, "Formula", "Base less implied"],
    ["", null, "", ""], ["Spot-implied revenue scale", data.reverse.implied_revenue_scale, "Python bisection", "Uniform scale; intentionally blunt"],
    ["Implied FY2027 revenue, $bn", data.reverse.implied_fy2027_revenue, "Solver output", "Not a company guide"], ["Implied FY2032 revenue, $bn", data.reverse.implied_fy2032_revenue, "Solver output", "At base margins and capital intensity"],
    ["Implied revenue CAGR", data.reverse.implied_revenue_cagr, "Solver output", "FY2026 to FY2032"],
  ];
  s.getRange("B5").formulas = [["=Drivers!B5"]]; s.getRange("B7").formulas = [[formulaValueAt("$B$6", "Scenarios!$C$27")]]; s.getRange("B8").formulas = [["=B7-B5"]];
  s.getRange("B9").formulas = [["=Scenarios!B27"]]; s.getRange("B10").formulas = [["=B9-B6"]];
  s.getRange("B5").format.numberFormat = fmt.currency; s.getRange("B6").format.numberFormat = fmt.pct2; s.getRange("B7:B8").format.numberFormat = fmt.currency; s.getRange("B9:B10").format.numberFormat = fmt.pct; s.getRange("B12").format.numberFormat = "0.000x"; s.getRange("B13:B14").format.numberFormat = fmt.bn; s.getRange("B15").format.numberFormat = fmt.pct;
  styleInputs(s, "B6"); styleInputs(s, "B12:B15"); s.getRange("B7:B8").format.fill = COLORS.paleTeal; s.getRange("A5:D15").format.wrapText = true; box(s, "A5:D15"); setWidths(s, { A: 38, B: 18, C: 22, D: 58 });
}

// ---------------------------------------------------------------------------
// Sensitivities
// ---------------------------------------------------------------------------
{
  const s = sheets.Sensitivities;
  title(s, "Base DCF sensitivity", "Value per share across WACC and terminal growth. Operating forecast, terminal ROIC and base bridge are held constant.", "G");
  s.getRange("A4:F4").merge(); s.getRange("A4:F4").values = [["Terminal growth →"]]; s.getRange("A4:F4").format.fill = COLORS.navy; s.getRange("A4:F4").format.font = { bold: true, color: COLORS.white };
  s.getRange("A5:F5").values = [["WACC ↓", 0.020, 0.025, 0.030, 0.035, 0.040]]; header(s, "A5:F5");
  s.getRange("B5:F5").format.numberFormat = fmt.pct;
  const waccs = [0.080, 0.090, 0.100, 0.107, 0.120];
  s.getRange("A6:A10").values = waccs.map((x) => [x]); s.getRange("A6:A10").format.numberFormat = fmt.pct;
  for (let row = 6; row <= 10; row++) for (let col = 1; col <= 5; col++) {
    const letter = String.fromCharCode(66 + col - 1);
    s.getRange(`${letter}${row}`).formulas = [[formulaValueAt(`$A${row}`, `${letter}$5`)]];
  }
  s.getRange("B6:F10").format.numberFormat = fmt.currency; box(s, "A5:F10");
  s.getRange("D9").format.fill = COLORS.paleTeal; s.getRange("D9").format.font = { bold: true, color: COLORS.teal };
  s.getRange("A13:G13").merge(); s.getRange("A13:G13").values = [["Read the grid as a duration diagnostic. The base cell is WACC 10.7% / g 3.0%; spot requires a materially lower discount rate on the same cash flows."]]; s.getRange("A13:G13").format.wrapText = true; s.getRange("A13:G13").format.fill = COLORS.soft;
  setWidths(s, { A: 16, B: 16, C: 16, D: 16, E: 16, F: 16, G: 42 });
}

// ---------------------------------------------------------------------------
// Decision
// ---------------------------------------------------------------------------
{
  const s = sheets.Decision;
  title(s, "Decision and capital gates", "A polished model is not permission to trade. Every gate below must be cleared at the decision time.", "D");
  s.getRange("A4:B4").values = [["Decision item", "Value"]]; header(s, "A4:B4");
  s.getRange("A5:A13").values = [["Spot"], ["Bear value"], ["Base value"], ["Bull value"], ["Base upside"], ["Required net return"], ["Long entry reference"], ["Open capital gates"], ["Position size"]];
  s.getRange("B5:B13").formulas = [["=Drivers!B5"], ["=Scenarios!H26"], ["=Scenarios!H27"], ["=Scenarios!H28"], ["=B7/B5-1"], ["=Drivers!B30"], ["=B7/(1+B10)"], ["=COUNTIF(C16:C22,\"OPEN\")"], ["=0"]];
  s.getRange("B5:B8").format.numberFormat = fmt.currency; s.getRange("B9:B10").format.numberFormat = fmt.pct; s.getRange("B11").format.numberFormat = fmt.currency; s.getRange("B12").format.numberFormat = fmt.integer; s.getRange("B13").format.numberFormat = "0.0%";
  s.getRange("A13:B13").format.fill = COLORS.paleTeal; s.getRange("A13:B13").format.font = { bold: true, color: COLORS.teal }; box(s, "A5:B13");
  s.getRange("A15:D15").values = [["Gate", "Required evidence", "Status", "Owner / timing"]]; header(s, "A15:D15");
  s.getRange("A16:D22").values = data.capital_gates.map(([gate, requirement, status]) => [gate, requirement, status, "PM / analyst before entry"]);
  s.getRange("C16:C22").format.fill = COLORS.paleRed; s.getRange("C16:C22").format.font = { bold: true, color: COLORS.red }; s.getRange("A16:D22").format.wrapText = true; box(s, "A16:D22");
  section(s, "A25:D25", "Conditional action rules");
  s.getRange("A26:D29").values = [
    ["Long", "Q2/guide establish upside to frozen consensus; demand-quality work clears; net return ≥20%", "THEN", "Re-underwrite value, hedge and event loss before sizing"],
    ["Short", "Reported demand or guide breaks base; revisions follow; uncapped upside is controlled; net downside ≥20%", "THEN", "Re-underwrite borrow, options, crowding and factor hedge"],
    ["Current", "No verified variant; base DCF below spot; bull state uncapped; all gates open", "ACTION", "WATCHLIST / NO POSITION"],
    ["Event date", "August 26 appears in prior market calendar, but official IR rate-limited this rebuild", "ACTION", "Reverify on official IR before relying on date"],
  ];
  s.getRange("A26:D29").format.wrapText = true; box(s, "A26:D29"); setWidths(s, { A: 23, B: 76, C: 14, D: 48 });
}

// ---------------------------------------------------------------------------
// Checks
// ---------------------------------------------------------------------------
{
  const s = sheets.Checks;
  title(s, "Model checks", "These controls cover the exact seams that failed in the prior version. Formula-error scans are also run outside Excel before circulation.", "C");
  s.getRange("A4:C4").values = [["Control", "Result", "Formula / threshold"]]; header(s, "A4:C4");
  s.getRange("A5:C15").values = [
    ["Scenario ordering", null, "Bear < Base < Bull"], ["WACC build rounds to base input", null, "Difference < 3bp"],
    ["WACC spread over terminal growth", null, "> 400bp"], ["Terminal ROIC exceeds growth", null, "ROIC > g"],
    ["FY2027 D&A floor", null, "> Q1 D&A + remaining amortization"], ["Q1 equity gains retained", null, "$15.936bn exactly"],
    ["April liquid balance ties", null, "$50.335bn exactly"], ["All capital gates imply zero size", null, "7 open and 0.0%"],
    ["No probability-weighted decision", null, "No expected-value row"], ["Base sensitivity center", null, "Matches base DCF"],
    ["Check failures", null, "Must equal zero"],
  ];
  s.getRange("B5:B14").formulas = [
    ["=IF(AND(Scenarios!H26<Scenarios!H27,Scenarios!H27<Scenarios!H28),\"PASS\",\"FAIL\")"],
    ["=IF(ABS(WACC!B14-Scenarios!B27)<0.0003,\"PASS\",\"FAIL\")"],
    ["=IF(Scenarios!B27-Scenarios!C27>4%,\"PASS\",\"FAIL\")"], ["=IF(Scenarios!D27>Scenarios!C27,\"PASS\",\"FAIL\")"],
    ["=IF(Depreciation!B25>Drivers!B14+Drivers!B15,\"PASS\",\"FAIL\")"], ["=IF(ABS(Drivers!B37-15.936)<0.001,\"PASS\",\"FAIL\")"],
    ["=IF(ABS(Drivers!B17-50.335)<0.001,\"PASS\",\"FAIL\")"], ["=IF(AND(Decision!B12=7,Decision!B13=0),\"PASS\",\"FAIL\")"],
    ["=IF(COUNTIF(Decision!A5:A13,\"*Expected*\")=0,\"PASS\",\"FAIL\")"], ["=IF(ABS(Sensitivities!D9-Scenarios!H27)<0.01,\"PASS\",\"FAIL\")"],
  ];
  s.getRange("B15").formulas = [["=COUNTIF(B5:B14,\"FAIL\")"]]; s.getRange("B15").format.numberFormat = fmt.integer;
  s.getRange("B5:B14").format.fill = COLORS.paleTeal; s.getRange("B5:B14").format.font = { bold: true, color: COLORS.teal }; s.getRange("A15:C15").format.fill = COLORS.soft; s.getRange("A15:C15").format.font = { bold: true };
  s.getRange("A5:C15").format.wrapText = true; box(s, "A5:C15"); setWidths(s, { A: 48, B: 15, C: 56 });
}

// ---------------------------------------------------------------------------
// Notes
// ---------------------------------------------------------------------------
{
  const s = sheets.Notes;
  title(s, "Conventions and limitations", "Read before using any output in an investment discussion.", "D");
  s.getRange("A4:D4").values = [["Topic", "Treatment", "Risk", "Required follow-up"]]; header(s, "A4:D4");
  s.getRange("A5:D14").values = [
    ["Units", "$bn except per-share values and percentages", "Mixing units can create silent errors", "Check source and number format"],
    ["Valuation date", "Aug. 7 market cut; Apr. 26 balance sheet", "Q2 balance sheet is not filed", "Refresh after Q2"],
    ["FY2027 stub", "Full-year FCFF less Q1 reported CFO less capex", "CFO less capex is an FCFF proxy", "Replace with filed Q2 bridge"],
    ["Revenue", "Consolidated scenarios", "No bottom-up current-platform forecast", "Build Data Center / Edge after enough reported history"],
    ["D&A", "Opening runoff plus forecast vintages", "Asset mix and lives are analyst assumptions", "Recalibrate to disclosures"],
    ["Terminal value", "NOPAT × (1 − g / ROIC)", "Still 48%–76% of EV", "Use sensitivity, not a point target"],
    ["Equity stakes", "Scenario haircuts by liquidity", "Carrying value and monetization differ", "Refresh holdings and lock-ups"],
    ["Consensus", "Frozen FMP annual snapshot", "No broker provenance or revision history", "Freeze canonical panel"],
    ["Scenarios", "Unweighted states", "No evidence-grade probabilities", "Do not compute expected value or Kelly"],
    ["Implementation", "Position fixed at zero", "No book, borrow, options or factor context", "Complete capital gates"],
  ];
  s.getRange("A5:D14").format.wrapText = true; box(s, "A5:D14"); setWidths(s, { A: 26, B: 54, C: 54, D: 48 });
}

// Global formatting and export.
for (const sheet of Object.values(sheets)) {
  const used = sheet.getUsedRange();
  used.format.autofitRows();
}

await fs.mkdir(path.join(repoRoot, "nvidia"), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(repoRoot, "nvidia/model.xlsx"));

console.log(`Saved ${path.join(repoRoot, "nvidia/model.xlsx")}`);
