# Feature & Cleaning Decision Record

Based on `docs/data_inspection.md` (generated from `ml/data/raw/ds_salaries.csv`, 607 rows, 0 missing values anywhere).

```text
Target: salary_in_usd

Features included: work_year, experience_level, employment_type, job_title,
                    employee_residence, remote_ratio, company_location, company_size

Features excluded: salary (raw, original-currency amount — leakage),
                    salary_currency (leakage in combination with `salary`),
                    Unnamed: 0 (row index re-saved as a column — no predictive value)

Leakage fields: salary, salary_currency
  Reason: salary + salary_currency + an implicit FX rate reconstruct salary_in_usd
  almost exactly. Keeping either as a model input would let the tree "cheat"
  instead of learning from job/experience/location signal.

Missing-value strategy: none required. Every column is 0% null (verified by
  inspection, not assumed). If a future data refresh introduces nulls, the
  cleaning pipeline must fail fast rather than silently impute, since no
  imputation strategy has been validated against this schema.

Duplicate policy: 0 full-row duplicates, but 42 rows are exact duplicates of
  another row once the meaningless index column is ignored. These are dropped
  in Phase 3, with the count logged in the cleaning report (not silently
  dropped) per prd.md FR-02.

Outlier policy: do NOT remove statistical (IQR) outliers in salary_in_usd
  (10 rows flagged, up to $600,000). These are plausible senior/executive
  compensation values, not impossible data (no non-positive salaries exist).
  Removing them would bias the model against legitimate high earners. Only
  genuinely impossible values (non-positive salary, unknown category codes)
  would be removed — inspection found none. The 44 IQR-flagged raw `salary`
  values are not a data quality concern since that column is excluded as
  leakage and never reaches the model.

High-cardinality policy: job_title (50), employee_residence (57), and
  company_location (50) unique values against 607 rows. Kept as-is and
  handled by OneHotEncoder(handle_unknown="ignore") in the ColumnTransformer
  rather than manual bucketing — a Decision Tree can split on the resulting
  sparse indicator columns without a hand-rolled "other" bucket, and
  handle_unknown="ignore" keeps the API robust against unseen categories at
  prediction time. This does mean Phase 7 (input-space coverage) will produce
  more unique observed tuples than a low-cardinality schema would.
```
