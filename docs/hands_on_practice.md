# Hands-on practice and resume evidence

The files are an AI-assisted portfolio build. A generated file does not establish your ability to operate a tool. Complete the practical tasks, save your native edits, and be ready to explain the calculations before listing tool proficiency.

## Excel

1. Open the actual workbook in the `excel` folder in Microsoft Excel. On Dashboard, change the amber segment selector and observe every KPI and the trend change. Restore All.
2. Select a SUMIFS formula in the monthly working table. Explain its sum range, month criterion and segment criterion. Explain why the weighted rate is a ratio of summed components rather than an average of percentages.
3. Edit a value in Monthly Data, confirm the affected total and chart change, then undo. Inputs are prepared Python aggregates; this workbook does not perform transaction-level ETL.
4. Insert a native PivotTable from MonthlySource in a new worksheet. Put segment in Rows and the project's additive amounts in Values. Confirm totals match Dashboard. This PivotTable is a practice exercise; a native PivotTable is not precreated in the delivered workbook.
5. Add a slicer to your new PivotTable, filter one segment, and save your workbook. Slicers on the new pivot do not control the formula dashboard, which has its own selector.
6. Complete the project-specific lab below. Explain what changed and why. Save a screenshot of Dashboard and the lab after the edits.

## Power BI

1. Open the source project on Windows in Power BI Desktop. Follow `powerbi/README.md` to set FolderPath and refresh. If your installed release rejects the generated source, use the supplied Power Query queries and DAX measures to build a native report.
2. Inspect the FactMonthly-to-DimDate and FactMonthly-to-DimSegment relationships. Explain many-to-one cardinality and single-direction filtering.
3. Explain each DAX SUM/DIVIDE measure. Add one measure independently, such as an additive total not already on the page.
4. Run the validation DAX query and reconcile with expected_totals.json. Apply a segment slicer and confirm card and chart values.
5. Explain the previous-month measure and blank handling on the first observed month. Save a tested `.pbix` and screenshots of Overview and Model view. Do not claim that this package already contains a verified PBIX.

## Tableau

1. Open the packaged workbook in Tableau Desktop/Public Desktop; follow `tableau/README.md` for connection repair or native reconstruction if needed.
2. Inspect dimensions and measures. Explain the difference between an aggregate calculated field and a row-level calculation.
3. Add a segment filter and apply it to all worksheets using the same source. Verify the dashboard changes and reconciles to the CSV.
4. Extend the detail worksheet with Measure Names/Measure Values to display all four KPIs. Check that ratio fields stay aggregate ratios.
5. Save a new native packaged workbook and Overview screenshot. Publication is optional. No Tableau account, publication or native execution has been performed by this package.

## Interview checks

- Why can a join multiply availability or revenue totals?
- Why are rates calculated from numerator and denominator sums?
- Where does cleaning happen, and how would you refresh each tool?
- What is synthetic about the data, and which conclusions need a real-world test?
- Which work was AI-assisted, and which changes can you demonstrate yourself?

## Evidence log

| Task | Your date | Evidence filename | Your explanation |
|---|---|---|---|
| Excel segment filtering and formula edit | | | |
| Excel PivotTable and slicer exercise | | | |
| Power BI native refresh and DAX check | | | |
| Tableau native open and synchronized filter | | | |
| Project-specific lab | | | |

## Resume wording

Current accurate project description:

> Created an AI-assisted analytics portfolio combining Python/SQL analysis, formula-driven Excel dashboards, and generated Power BI and Tableau source assets.

After you complete native Power BI/Tableau checks and the hands-on tasks, you can describe the work you can demonstrate, for example:

> Built and validated KPI dashboards in Excel, Power BI and Tableau, using SUMIFS, DAX measures, dimensional relationships and aggregate calculated fields.

List the specific skills you can reproduce. Avoid Advanced/Expert labels until your own practical work supports them. All datasets are synthetic; present these as independent portfolio case studies.

## Credit lab

- Excel Policy Lab: change PD cutoff from the validation-selected value to 0. Approval rate and contribution must both become zero. Restore the cutoff. Change nondefault yield and explain the contribution change; predicted PD remains unchanged.
- The historical Dashboard retains the original Python-selected policy. The Policy Lab is a separate hypothetical scenario; do not mix their approval rates.
- Power BI/Tableau: filter Contract and reconcile default rate with defaults/applications, not the mean of monthly rates.
- Extend a native report with calibration.csv. Explain why good ROC AUC does not imply calibrated probabilities. This extension is a practice task.
