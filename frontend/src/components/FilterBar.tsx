import type { FilterOptions, ResultFilters } from "../lib/queries";
import { EMPLOYMENT_TYPE_LABELS, COMPANY_SIZE_LABELS, EXPERIENCE_LEVEL_LABELS, remoteRatioLabel, labelFor } from "../lib/format";

interface FilterBarProps {
  options: FilterOptions;
  filters: ResultFilters;
  onChange: (filters: ResultFilters) => void;
}

export function FilterBar({ options, filters, onChange }: FilterBarProps) {
  const hasActiveFilters = Object.values(filters).some((v) => v !== undefined && v !== "");

  return (
    <div className="filter-bar">
      <div className="filter-bar__row">
        <label className="filter-field">
          <span className="filter-field__label">Experience</span>
          <select
            value={filters.experienceLevel ?? ""}
            onChange={(e) => onChange({ ...filters, experienceLevel: e.target.value || undefined })}
          >
            <option value="">All levels</option>
            {options.experienceLevels.map((level) => (
              <option key={level} value={level}>
                {labelFor(EXPERIENCE_LEVEL_LABELS, level)}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span className="filter-field__label">Employment</span>
          <select
            value={filters.employmentType ?? ""}
            onChange={(e) => onChange({ ...filters, employmentType: e.target.value || undefined })}
          >
            <option value="">All types</option>
            {options.employmentTypes.map((type) => (
              <option key={type} value={type}>
                {labelFor(EMPLOYMENT_TYPE_LABELS, type)}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span className="filter-field__label">Company size</span>
          <select
            value={filters.companySize ?? ""}
            onChange={(e) => onChange({ ...filters, companySize: e.target.value || undefined })}
          >
            <option value="">All sizes</option>
            {options.companySizes.map((size) => (
              <option key={size} value={size}>
                {labelFor(COMPANY_SIZE_LABELS, size)}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span className="filter-field__label">Remote</span>
          <select
            value={filters.remoteRatio ?? ""}
            onChange={(e) => onChange({ ...filters, remoteRatio: e.target.value === "" ? undefined : Number(e.target.value) })}
          >
            <option value="">All arrangements</option>
            {options.remoteRatios.map((ratio) => (
              <option key={ratio} value={ratio}>
                {remoteRatioLabel(ratio)}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field filter-field--grow">
          <span className="filter-field__label">Job title</span>
          <input
            list="job-title-options"
            placeholder="Search job titles…"
            value={filters.jobTitle ?? ""}
            onChange={(e) => onChange({ ...filters, jobTitle: e.target.value || undefined })}
          />
          <datalist id="job-title-options">
            {options.jobTitles.map((title) => (
              <option key={title} value={title} />
            ))}
          </datalist>
        </label>

        {hasActiveFilters && (
          <button type="button" className="button button--ghost" onClick={() => onChange({})}>
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
