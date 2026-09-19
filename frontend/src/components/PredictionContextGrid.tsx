import { EMPLOYMENT_TYPE_LABELS, COMPANY_SIZE_LABELS, EXPERIENCE_LEVEL_LABELS, labelFor, remoteRatioLabel } from "../lib/format";
import type { SalaryResult } from "../lib/schemas";

export function PredictionContextGrid({ result }: { result: SalaryResult }) {
  const entries: [string, string][] = [
    ["Job title", result.job_title],
    ["Experience", labelFor(EXPERIENCE_LEVEL_LABELS, result.experience_level)],
    ["Employment type", labelFor(EMPLOYMENT_TYPE_LABELS, result.employment_type)],
    ["Company size", labelFor(COMPANY_SIZE_LABELS, result.company_size)],
    ...(result.remote_ratio !== null ? ([["Remote arrangement", remoteRatioLabel(result.remote_ratio)]] as [string, string][]) : []),
    ...(result.work_year !== null ? ([["Work year", String(result.work_year)]] as [string, string][]) : []),
    ...(result.employee_residence ? ([["Employee residence", result.employee_residence]] as [string, string][]) : []),
    ...(result.company_location ? ([["Company location", result.company_location]] as [string, string][]) : []),
  ];

  return (
    <dl className="context-grid">
      {entries.map(([term, value]) => (
        <div className="context-grid__item" key={term}>
          <dt>{term}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
