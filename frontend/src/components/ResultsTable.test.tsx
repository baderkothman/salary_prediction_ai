import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ResultsTable } from "./ResultsTable";
import type { SalaryResult } from "../lib/schemas";

function makeResult(overrides: Partial<SalaryResult> = {}): SalaryResult {
  return {
    id: "1",
    run_id: "run-1",
    feature_signature: "sig-1",
    work_year: 2022,
    experience_level: "SE",
    employment_type: "FT",
    job_title: "Data Scientist",
    employee_residence: "US",
    remote_ratio: 100,
    company_location: "US",
    company_size: "M",
    features: {},
    predicted_salary_usd: 147754.79,
    analysis_headline: null,
    analysis_summary: null,
    key_insights: null,
    chart_spec: null,
    analysis_context: null,
    limitations: null,
    created_at: "2026-09-19T00:00:00Z",
    ...overrides,
  };
}

function renderTable(results: SalaryResult[]) {
  return render(
    <MemoryRouter>
      <ResultsTable results={results} />
    </MemoryRouter>
  );
}

describe("ResultsTable", () => {
  it("renders a row per result with formatted salary and human labels", () => {
    renderTable([makeResult()]);

    expect(screen.getAllByText("Data Scientist").length).toBeGreaterThan(0);
    expect(screen.getAllByText("$147,755").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Senior-level").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Remote").length).toBeGreaterThan(0);
  });

  it("renders nothing but headers for an empty result set", () => {
    renderTable([]);
    expect(screen.queryByText("Data Scientist")).not.toBeInTheDocument();
  });

  it("links each row to its detail page", () => {
    renderTable([makeResult({ id: "abc-123" })]);
    const links = screen.getAllByRole("link");
    expect(links.some((link) => link.getAttribute("href") === "/results/abc-123")).toBe(true);
  });
});
