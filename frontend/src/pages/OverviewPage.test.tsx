import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as queries from "../lib/queries";
import { OverviewPage } from "./OverviewPage";

vi.mock("../lib/queries", async () => {
  const actual = await vi.importActual<typeof import("../lib/queries")>("../lib/queries");
  return {
    ...actual,
    useLatestPublishedRun: vi.fn(),
    useOverviewStats: vi.fn(),
  };
});

const mockedUseLatestPublishedRun = vi.mocked(queries.useLatestPublishedRun);
const mockedUseOverviewStats = vi.mocked(queries.useOverviewStats);

function renderPage() {
  return render(
    <MemoryRouter>
      <OverviewPage />
    </MemoryRouter>
  );
}

const PUBLISHED_RUN = {
  id: "run-1",
  status: "published" as const,
  model_version: "2026-09-19.1",
  dataset_hash: "hash",
  llm_model: "llama3.2:latest",
  prompt_version: "v1",
  model_metrics: {
    train: { mae: 34084.1, rmse: 49757.9, r2: 0.54 },
    test: { mae: 34506.8, rmse: 48108.7, r2: 0.488 },
  },
  coverage_summary: null,
  created_at: "2026-09-19T00:00:00Z",
  published_at: "2026-09-19T01:00:00Z",
};

const STATS = {
  count: 357,
  medianSalary: 120000,
  minSalary: 20000,
  maxSalary: 400000,
  distinctJobTitles: 42,
  byExperienceLevel: [{ label: "EN", value: 56000 }],
  byCompanySize: [{ label: "M", value: 120000 }],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("OverviewPage", () => {
  it("shows an empty state when there is no published run", () => {
    mockedUseLatestPublishedRun.mockReturnValue({ isPending: false, isError: false, data: null } as never);
    mockedUseOverviewStats.mockReturnValue({ data: undefined } as never);

    renderPage();

    expect(screen.getByText(/No published salary dataset is available yet/)).toBeInTheDocument();
  });

  it("shows an error state when the run query fails", () => {
    mockedUseLatestPublishedRun.mockReturnValue({
      isPending: false,
      isError: true,
      error: new Error("network down"),
      data: undefined,
    } as never);
    mockedUseOverviewStats.mockReturnValue({ data: undefined } as never);

    renderPage();

    expect(screen.getByText("network down")).toBeInTheDocument();
  });

  it("renders KPI cards and metrics once the run and stats have loaded", () => {
    mockedUseLatestPublishedRun.mockReturnValue({ isPending: false, isError: false, data: PUBLISHED_RUN } as never);
    mockedUseOverviewStats.mockReturnValue({ data: STATS } as never);

    renderPage();

    expect(screen.getByText("357")).toBeInTheDocument();
    expect(screen.getByText("$120,000")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText(/Model 2026-09-19.1/)).toBeInTheDocument();
  });
});
