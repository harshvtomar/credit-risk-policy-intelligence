# Methodology and limitations


1. Seed 73 generates 10,000 applications with a known synthetic default process. All 12-month outcomes mature by December 2025. Labels reflect simulation, not bureau data.
2. Split by origination month: 2023 train; January–June 2024 validation; July–December 2024 test. Income median imputation, standardization, and categorical encoding are fitted exclusively on training data.
3. Logistic regression uses income, debt-to-income, credit score, loan amount, prior delinquency count, and employment. Audit group and outcome are excluded. Coefficients describe model associations, not causal effects.
4. Policy threshold maximizes observed validation contribution over fixed cutoffs 0.02–0.50. The selected threshold is frozen before test scoring. This has selection noise and merits further validation.
5. Contribution assumes 12% principal earned on nondefault and 65% principal lost on default; rejects earn zero. It excludes funding, timing, servicing, and capital costs. Full outcomes on rejected applicants exist only because the data is synthetic.
6. ROC AUC measures ranking, average precision is compared with prevalence, Brier score measures squared probability error, and quantile calibration bins check probability reliability.
7. Population stability index uses training-derived deciles and smoothing; missing-value shifts are separately reported. PSI is a descriptive diagnostic, not a significance test or definitive drift threshold.
8. Group audit reports approval, default prevalence, rejection true-positive and false-positive rates, and Brier score. No confidence intervals, legal compliance conclusion, or fairness guarantee is claimed.
