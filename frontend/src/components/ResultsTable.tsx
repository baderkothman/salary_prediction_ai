import { Link } from "react-router-dom";

import type { SalaryResult } from "../lib/schemas";
import { EMPLOYMENT_TYPE_LABELS, EXPERIENCE_LEVEL_LABELS, formatCurrency, labelFor, remoteRatioLabel } from "../lib/format";

export function ResultsTable({ results }: { results: SalaryResult[] }) {
  return (
    <>
      <table className="results-table results-table--desktop">
        <thead>
          <tr>
            <th>Job title</th>
            <th>Experience</th>
            <th>Employment</th>
            <th>Company size</th>
            <th>Remote</th>
            <th className="results-table__salary-col">Predicted salary</th>
            <th aria-label="Details" />
          </tr>
        </thead>
        <tbody>
          {results.map((row) => (
            <tr key={row.id}>
              <td>{row.job_title}</td>
              <td>{labelFor(EXPERIENCE_LEVEL_LABELS, row.experience_level)}</td>
              <td>{labelFor(EMPLOYMENT_TYPE_LABELS, row.employment_type)}</td>
              <td>{row.company_size}</td>
              <td>{row.remote_ratio !== null ? remoteRatioLabel(row.remote_ratio) : "—"}</td>
              <td className="results-table__salary-col tabular-nums">{formatCurrency(row.predicted_salary_usd)}</td>
              <td>
                <Link to={`/results/${row.id}`} className="results-table__link">
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <ul className="results-cards results-cards--mobile">
        {results.map((row) => (
          <li key={row.id} className="results-card">
            <Link to={`/results/${row.id}`} className="results-card__link">
              <div className="results-card__top">
                <span className="results-card__title">{row.job_title}</span>
                <span className="results-card__salary tabular-nums">{formatCurrency(row.predicted_salary_usd)}</span>
              </div>
              <div className="results-card__meta">
                {labelFor(EXPERIENCE_LEVEL_LABELS, row.experience_level)} · {labelFor(EMPLOYMENT_TYPE_LABELS, row.employment_type)} ·{" "}
                {row.company_size} · {row.remote_ratio !== null ? remoteRatioLabel(row.remote_ratio) : "—"}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
