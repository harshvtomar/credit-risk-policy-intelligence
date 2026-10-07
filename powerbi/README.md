# Power BI source project

**Status: source files generated; Power BI Desktop open, refresh, DAX execution and visual checks are pending. This is not a validated PBIX.**

## Open and validate

1. Use current Power BI Desktop on Windows. This package contains a `.pbip` shortcut, PBIR report definitions, and a TMSL semantic model.
2. Extract the complete repository. Keep `bi/data` and `powerbi` folders intact. Open `credit_risk_policy_intelligence.pbip`. If the installed release requests a format upgrade, allow it and save a copy.
3. Transform Data → Manage Parameters → set `FolderPath` to this repository's `bi/data` folder with a trailing separator. Default is `C:\Analytics\credit-risk-policy-intelligence\bi\data\`. No credentials are required for the local synthetic CSV files.
4. Close & Apply, then Refresh. The model has **FactMonthly**, a daily **DimDate**, and **DimSegment**, with single-direction many-to-one relationships. Mark DimDate[Date] as the date table if your release requires it for time intelligence.
5. Check the Overview page: four KPI cards, month trend, segment comparison, segment slicer, and detail table. Verify the slicer affects the cards and trend.
6. Run `validation_query.dax` in DAX Query View and compare with `expected_totals.json`. Filter each segment and compare with `outputs/monthly_kpis.csv`. Do not average monthly percentages.
7. Import `theme.json` if desired. Save as `.pbix` via File → Save As after successful refresh and checks. Take screenshots of both Overview and Model view for the portfolio.

If the source project does not open in your installed version, use a new report and paste the supplied Power Query `.pq` files through Advanced Editor, create the FolderPath text parameter, then add the supplied DAX measures and relationships. Recreate the Overview layout using the visual list in `report_layout.md`. This fallback is a native build exercise, not evidence of a previously verified report.

Data is a prepared monthly aggregate, not transaction-level Power Query ETL. The Python pipeline owns transaction cleaning and complex cohort/risk/operational analysis.

References: [Microsoft PBIP documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [semantic model format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset), [PBIR report format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report).
