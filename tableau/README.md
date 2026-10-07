# Tableau workbook sources

**Status: generated XML and packaged CSV are structurally checked. Tableau Desktop/Public open, calculated-field execution, filter configuration, visual layout and native save are pending.**

Files: `.twb` workbook, `.twbx` packaged workbook containing `Data/monthly.csv`, `.tds` datasource, and explicit calculated-field definitions. The XML uses the documented sample workbook convention from Tableau's official document-api examples; newer Tableau releases may upgrade the format.

## Native verification

1. Open `credit-risk-policy-intelligence.twbx` in Tableau Desktop or Tableau Public Desktop. If the CSV is not located automatically, Edit Connection and select `Data/monthly.csv`.
2. Check Month Date is a date; Month and Segment are dimensions; all numeric source columns are measures.
3. Inspect the four aggregate calculated fields. Rates must divide summed numerators by summed denominators.
4. Open Overview and verify four KPI worksheets, monthly trend, segment comparison and detail. Use the month field in chronological order and a zero baseline on the bar chart. The detail sheet initially shows the lead measure; add the remaining three measures through Measure Names/Measure Values as a practical extension.
5. On Monthly detail, drag Segment to Filters, choose all values, then Show Filter. Apply to Worksheets → All Using This Data Source. Add the filter card to the Overview dashboard. Filter synchronization is intentionally a native validation/practice step.
6. Reconcile KPI totals against `../powerbi/expected_totals.json` and each segment against `../outputs/monthly_kpis.csv`. Fix any native-open or rendering issue before describing this as a tested Tableau dashboard.
7. Save a new packaged workbook in Tableau and take an Overview screenshot. Publishing to Tableau Public is optional and exposes the included synthetic data publicly.

If this generated workbook requires repair in your release, create a new workbook from the included CSV and reproduce the listed worksheets using `calculated_fields.txt`. No tested screenshots or native engine result is claimed by this source-generation step.

References: [Tableau file formats](https://help.tableau.com/current/pro/desktop/en-us/environ_filesandfolders.htm), [official document-api examples](https://github.com/tableau/document-api-python/tree/master/samples).
