# Dataset Inspection Report

Generated: 2026-09-19T17:49:19.454275+00:00

- Source file: `ml/data/raw/ds_salaries.csv`
- SHA-256: `6462a0cfed466651f9109f429d696e3d0a58f9a909130177a242c6a6665b05f6`
- Rows: 607
- Columns: 12

## Columns

| Column | Dtype | Nulls | Null % | Unique |
|---|---|---:|---:|---:|
| Unnamed: 0 | int64 | 0 | 0.0% | 607 |
| work_year | int64 | 0 | 0.0% | 3 |
| experience_level | str | 0 | 0.0% | 4 |
| employment_type | str | 0 | 0.0% | 4 |
| job_title | str | 0 | 0.0% | 50 |
| salary | int64 | 0 | 0.0% | 272 |
| salary_currency | str | 0 | 0.0% | 17 |
| salary_in_usd | int64 | 0 | 0.0% | 369 |
| employee_residence | str | 0 | 0.0% | 57 |
| remote_ratio | int64 | 0 | 0.0% | 3 |
| company_location | str | 0 | 0.0% | 50 |
| company_size | str | 0 | 0.0% | 3 |

## Duplicates

- Full-row duplicates: 0
- Duplicates ignoring `Unnamed: 0` index column: 42

## Numeric profile

| Column | Min | Max | Mean | Median | Std | IQR outliers |
|---|---:|---:|---:|---:|---:|---:|
| work_year | 2020 | 2022 | 2021.4 | 2022 | 0.7 | 0 |
| salary | 4000 | 30400000 | 324000.1 | 115000 | 1544357.5 | 44 |
| salary_in_usd | 2859 | 600000 | 112297.9 | 101570 | 70957.3 | 10 |
| remote_ratio | 0 | 100 | 70.9 | 100 | 40.7 | 0 |

## Categorical cardinality

| Column | Unique values |
|---|---:|
| experience_level | 4 |
| employment_type | 4 |
| job_title | 50 |
| salary_currency | 17 |
| employee_residence | 57 |
| remote_ratio | 3 |
| company_location | 50 |
| company_size | 3 |

## Invalid value checks

- Non-positive `salary_in_usd`: 0
- Non-positive `salary`: 0
- Unexpected `experience_level` values: none
- Unexpected `employment_type` values: none
- Unexpected `company_size` values: none
- Unexpected `remote_ratio` values: none

## Decision record

- Target: `salary_in_usd`
- Leakage candidates (excluded from features): salary, salary_currency
- Redundant columns (dropped): Unnamed: 0
- High-cardinality columns (>20 unique values): job_title, employee_residence, company_location
