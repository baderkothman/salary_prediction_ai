import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../lib/api";
import { PredictPage } from "./PredictPage";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return { ...actual, fetchModelInfo: vi.fn(), fetchPrediction: vi.fn(), fetchNarrative: vi.fn() };
});

const mockedFetchModelInfo = vi.mocked(api.fetchModelInfo);
const mockedFetchPrediction = vi.mocked(api.fetchPrediction);
const mockedFetchNarrative = vi.mocked(api.fetchNarrative);

const MODEL_INFO: api.ModelInfo = {
  model_name: "decision_tree_salary_regressor",
  model_version: "2026-09-19.1",
  target: "salary_in_usd",
  feature_columns: [],
  categorical_domains: {
    experience_level: ["EN", "SE"],
    employment_type: ["FT"],
    company_size: ["S", "M", "L"],
    job_title: ["Data Scientist"],
    employee_residence: ["US"],
    company_location: ["US"],
  },
  numeric_ranges: {
    work_year: { min: 2020, max: 2022 },
    remote_ratio: { min: 0, max: 100, allowed_values: [0, 50, 100] },
  },
  metrics: { mae: 34506.8, rmse: 48108.7, r2: 0.488 },
  trained_at: "2026-09-19T00:00:00Z",
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <PredictPage />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedFetchModelInfo.mockResolvedValue(MODEL_INFO);
});

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.selectOptions(screen.getByLabelText("Experience"), "SE");
  await user.selectOptions(screen.getByLabelText("Employment"), "FT");
  await user.selectOptions(screen.getByLabelText("Company size"), "M");
  await user.selectOptions(screen.getByLabelText("Remote"), "100");
  await user.clear(screen.getByLabelText("Work year"));
  await user.type(screen.getByLabelText("Work year"), "2022");
  await user.type(screen.getByLabelText("Job title"), "Data Scientist");
  await user.type(screen.getByLabelText("Employee residence"), "US");
  await user.type(screen.getByLabelText("Company location"), "US");
}

describe("PredictPage", () => {
  it("shows an error state when the model info API is unreachable", async () => {
    mockedFetchModelInfo.mockReset();
    mockedFetchModelInfo.mockRejectedValue(new Error("network error"));
    renderPage();

    await waitFor(() => expect(screen.getByText(/Could not reach the prediction API/)).toBeInTheDocument());
  });

  it("disables the submit button until the form is fully filled (form validation)", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByRole("button", { name: /predict/i })).toBeInTheDocument());

    const submitButton = screen.getByRole("button", { name: /predict/i });
    expect(submitButton).toBeDisabled();

    const user = userEvent.setup();
    await fillValidForm(user);

    expect(submitButton).toBeEnabled();
  });

  it("submits both prediction and narrative requests and renders a successful result", async () => {
    mockedFetchPrediction.mockResolvedValue({
      prediction: 147754.79,
      currency: "USD",
      model_version: "2026-09-19.1",
      inputs: {} as api.PredictionInputs,
    });
    mockedFetchNarrative.mockResolvedValue({
      prediction: 147754.79,
      currency: "USD",
      model_version: "2026-09-19.1",
      headline: "Above the peer median",
      summary: "This prediction sits above the peer median for comparable roles.",
      insights: ["Matches senior-level trends."],
      comparison: "Above the median.",
      limitations: ["Small sample size."],
      chart: { type: "bar", title: "Median by level", x: ["SE"], y: [140000] },
      supporting_stats: { sample_size: 49, median_salary_usd: 144000 },
      percentile_rank_in_dataset: 74,
    });

    renderPage();
    await waitFor(() => expect(screen.getByRole("button", { name: /predict/i })).toBeInTheDocument());

    const user = userEvent.setup();
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /predict/i }));

    // TanStack Query's mutationFn is invoked with a second (context) argument
    // it manages internally -- only the first argument is our actual input.
    expect(mockedFetchPrediction.mock.calls[0][0]).toEqual(
      expect.objectContaining({ experience_level: "SE", job_title: "Data Scientist" })
    );
    expect(mockedFetchNarrative).toHaveBeenCalled();

    await waitFor(() => expect(screen.getByText(/\$147,755 predicted salary/)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText("Above the peer median")).toBeInTheDocument());
  });

  it("shows a loading indicator while the narrative is generating, and an error state if it fails", async () => {
    mockedFetchPrediction.mockResolvedValue({
      prediction: 100000,
      currency: "USD",
      model_version: "v",
      inputs: {} as api.PredictionInputs,
    });
    let rejectNarrative!: (err: unknown) => void;
    mockedFetchNarrative.mockReturnValue(new Promise((_resolve, reject) => (rejectNarrative = reject)));

    renderPage();
    await waitFor(() => expect(screen.getByRole("button", { name: /predict/i })).toBeInTheDocument());

    const user = userEvent.setup();
    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /predict/i }));

    expect(await screen.findByText(/Generating analysis/)).toBeInTheDocument();

    rejectNarrative(new api.ApiError(503, "OLLAMA_UNAVAILABLE", "Could not reach the local Ollama instance"));

    expect(await screen.findByText("Could not reach the local Ollama instance")).toBeInTheDocument();
  });
});
