-- SQLite. Outcome rows are fully matured to 2025-12-31.
SELECT origination_month, employment, COUNT(*) AS applications,
       AVG(default_12m) AS default_rate, AVG(loan_amount) AS mean_loan
FROM applications GROUP BY 1,2 ORDER BY 1,2;

-- Time-window population and missingness checks.
SELECT CASE WHEN origination_month < '2024-01' THEN 'train'
            WHEN origination_month < '2024-07' THEN 'validation' ELSE 'test' END AS split,
       COUNT(*) AS applications, AVG(default_12m) AS default_rate,
       1.0*SUM(annual_income IS NULL)/COUNT(*) AS missing_income_rate
FROM applications GROUP BY 1;

-- Application-month exposure and sequential change.
WITH exposure AS (SELECT origination_month,SUM(loan_amount) AS exposure,COUNT(*) AS n FROM applications GROUP BY 1)
SELECT *,exposure-LAG(exposure) OVER(ORDER BY origination_month) AS monthly_exposure_change FROM exposure;
