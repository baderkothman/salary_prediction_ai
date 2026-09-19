import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as queries from "../lib/queries";
import { ResultDetailPage } from "./ResultDetailPage";
import type { SalaryResult } from "../lib/schemas";

vi.mock("../lib/queries", async () => {
  const actual = await vi.importActual<typeof import("../lib/queries")>("../lib/queries");
  return { ...actual, useSalaryResult: vi.fn() };
});

const mockedUseSalaryResult = vi.mocked(queries.useSalaryResult);

function baseResult(overrides: Partial<SalaryResult> = {}): SalaryResult {
  return {
    id: "abc",
    run_id: "run-1",
    feature_signature: "sig",
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

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/results/abc"]}>
      <Routes>
        <Route path="/results/:id" element={<ResultDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.clearAllMocks());

describe("ResultDetailPage", () => {
  it("renders the prediction header and job title", () => {
    mockedUseSalaryResult.mockReturnValue({ isPending: false, isError: false, data: baseResult() } as never);
    renderPage();

    expect(screen.getByRole("heading", { name: "Data Scientist" })).toBeInTheDocument();
    expect(screen.getByText(/\$147,755 predicted salary/)).toBeInTheDocument();
  });

  it("shows a no-narrative message when the row was not sampled for LLM analysis", () => {
    mockedUseSalaryResult.mockReturnValue({ isPending: false, isError: false, data: baseResult() } as never);
    renderPage();

    expect(screen.getByText(/No narrative generated for this prediction/)).toBeInTheDocument();
  });

  it("renders the narrative when present", () => {
    mockedUseSalaryResult.mockReturnValue({
      isPending: false,
      isError: false,
      data: baseResult({
        analysis_headline: "Above the peer median",
        analysis_summary: "This prediction sits above the comparable peer median.",
        key_insights: ["Insight one"],
        limitations: ["Small sample size"],
      }),
    } as never);
    renderPage();

    expect(screen.getByText("Above the peer median")).toBeInTheDocument();
    expect(screen.getByText("Insight one")).toBeInTheDocument();
    expect(screen.getByText("Small sample size")).toBeInTheDocument();
  });

  it("renders a valid chart_spec as a chart", () => {
    mockedUseSalaryResult.mockReturnValue({
      isPending: false,
      isError: false,
      data: baseResult({
        chart_spec: { type: "bar", title: "Median by level", x: ["EN", "SE"], y: [56000, 140000] },
      }),
    } as never);
    renderPage();

    expect(screen.getByText("Median by level")).toBeInTheDocument();
  });

  it("renders the invalid-chart fallback instead of crashing on a malformed chart_spec", () => {
    mockedUseSalaryResult.mockReturnValue({
      isPending: false,
      isError: false,
      data: baseResult({
        // @ts-expect-error -- deliberately malformed to test the fallback path
        chart_spec: { type: "pie", title: "bad", x: ["a"], y: [1, 2] },
      }),
    } as never);
    renderPage();

    expect(screen.getByText(/couldn't be displayed/)).toBeInTheDocument();
  });

  it("shows an empty state when the result cannot be found", () => {
    mockedUseSalaryResult.mockReturnValue({ isPending: false, isError: false, data: null } as never);
    renderPage();

    expect(screen.getByText("Prediction not found")).toBeInTheDocument();
  });
});
