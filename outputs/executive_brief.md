# Credit risk decision brief

Synthetic educational analysis. No deployment or real lending recommendation.

- Out-of-time ROC AUC: 0.737; average precision: 0.520, compared with default prevalence 27.5%. Brier score: 0.173.
- Validation selects a PD cutoff of 0.16; the held-out test approval rate is 42.2%.
- Test policy contribution: $419,270; approve-all comparison: $-4,930,493. These depend on assumed 12% nondefault contribution and 65% loss given default, not comprehensive loan cash flows.
- Review calibration and group rejection error rates before considering any operational pilot. Group attributes are excluded from model features; this alone does not establish fairness.

All simulated applicants have outcomes, including those rejected by the hypothetical policy. Real underwriting data typically lacks rejected-applicant outcomes, so this comparison cannot directly transfer to production. The dataset contains fully matured 12-month outcomes; cutoff is December 2025. Missing-income imputation is fitted on training data only. Group differences have no significance or causal claim.
