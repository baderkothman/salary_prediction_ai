import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as queries from "../lib/queries";
import { ExplorePage } from "./ExplorePage";
import type { SalaryResult } from "../lib/schemas";

vi.mock("../lib/queries", async () => {
  const actual = await vi.importActual<typeof import("../lib/queries")>("../lib/queries");
  return {
    ...actual,
    useLatestPublishedRun: vi.fn(),
    useFilterOptions: vi.fn(),
    useSalaryResults: vi.fn(),
  };
});

const mockedUseLatestPublishedRun = vi.mocked(queries.useLatestPublishedRun);
const mockedUseFilterOptions = vi.mocked(queries.useFilterOptions);
const mockedUseSalaryResults = vi.mocked(queries.useSalaryResults);

const RUN = { id: "run-1", status: "published" as const } as never;

const OPTIONS = {
  experienceLevels: ["EN", "SE"],
  employmentTypes: ["FT"],
  companySizes: ["S", "M", "L"],
  remoteRatios: [0, 50, 100],
  jobTitles: ["Data Scientist"],
};

function makeResult(overrides: Partial<SalaryResult> = {}): SalaryResult {
  return {
    id: "1",
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
    predicted_salary_usd: 150000,
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
    <MemoryRouter>
      <ExplorePage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedUseLatestPublishedRun.mockReturnValue({ isPending: false, isError: false, data: RUN } as never);
  mockedUseFilterOptions.mockReturnValue({ data: OPTIONS } as never);
});

describe("ExplorePage", () => {
  it("shows a not-an-error empty state when filters match nothing", () => {
    mockedUseSalaryResults.mockReturnValue({
      data: { rows: [], total: 0 },
      isError: false,
      isLoading: false,
    } as never);

    renderPage();

    expect(screen.getByText("No predictions match these filters")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders matching results and a summary count", () => {
    mockedUseSalaryResults.mockReturnValue({
      data: { rows: [makeResult()], total: 1 },
      isError: false,
      isLoading: false,
    } as never);

    renderPage();

    expect(screen.getByText(/1 matching predictions/)).toBeInTheDocument();
    expect(screen.getAllByText("Data Scientist").length).toBeGreaterThan(0);
  });

  it("shows an error state if the results query fails", () => {
    mockedUseSalaryResults.mockReturnValue({
      data: undefined,
      isError: true,
      error: new Error("query failed"),
      isLoading: false,
    } as never);

    renderPage();

    expect(screen.getByText("query failed")).toBeInTheDocument();
  });
});
