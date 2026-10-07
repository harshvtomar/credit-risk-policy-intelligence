# Source data dictionary

All datasets are synthetic; blank values mean missing, not zero.

## applications.csv

| Field | Meaning |
|---|---|
| `application_id` | Unique application identifier. |
| `origination_month` | Application cohort in YYYY-MM. |
| `annual_income` | Annual USD income; some values are intentionally missing. |
| `debt_to_income` | Fractional debt-to-income ratio. |
| `credit_score` | Simulated numerical credit score. |
| `loan_amount` | Requested USD principal. |
| `prior_delinquencies` | Count of previous delinquencies. |
| `employment` | Employment category. |
| `audit_group` | Synthetic group marker, for auditing only; not a predictor. |
| `default_12m` | Binary default outcome over the following 12 months; fully matured. |
