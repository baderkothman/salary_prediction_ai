import { describe, expect, it } from "vitest";

import { ChartSpecSchema, PipelineRunSchema } from "./schemas";

describe("PipelineRunSchema", () => {
  // Regression test: model_metrics is stored exactly as
  // ml/src/training/train.py writes model_metadata.json's "metrics" field
  // (nested {train, test}), not the flat {mae, rmse, r2} shape a prior
  // version of this schema assumed. That mismatch shipped past every
  // mocked component test because the mocks used the same wrong shape as
  // the schema -- only pulling a real row from Supabase caught it. This
  // fixture is copied verbatim from a real `pipeline_runs` row.
  it("accepts the real shape persisted by scripts/persist.py", () => {
    const realRow = {
      id: "ae4fb570-77c7-4110-9e99-bb2c84df481f",
      status: "published",
      model_version: "2026-09-19.1",
      dataset_hash: "6462a0cfed466651f9109f429d696e3d0a58f9a909130177a242c6a6665b05f6",
      llm_model: "llama3.2:latest",
      prompt_version: "v1",
      model_metrics: {
        test: { r2: 0.48778454323247167, mae: 34506.84337133029, rmse: 48108.74587929711 },
        train: { r2: 0.5404491983773563, mae: 34084.10442375869, rmse: 49757.93216051622 },
      },
      coverage_summary: null,
      created_at: "2026-09-19T18:18:59.123456+00:00",
      published_at: "2026-09-20T00:21:45.678000+00:00",
    };

    const result = PipelineRunSchema.safeParse(realRow);
    expect(result.success).toBe(true);
  });

  it("rejects a flat model_metrics shape (the bug this test guards against)", () => {
    const result = PipelineRunSchema.safeParse({
      id: "x",
      status: "published",
      model_version: "v",
      dataset_hash: "h",
      llm_model: "m",
      prompt_version: "v1",
      model_metrics: { mae: 1, rmse: 1, r2: 1 },
      coverage_summary: null,
      created_at: "2026-09-19T00:00:00Z",
      published_at: null,
    });
    expect(result.success).toBe(false);
  });
});

describe("ChartSpecSchema", () => {
  it("accepts a valid bar chart spec", () => {
    const result = ChartSpecSchema.safeParse({
      type: "bar",
      title: "Median salary by experience level",
      x: ["Entry", "Senior"],
      y: [60000, 140000],
    });
    expect(result.success).toBe(true);
  });

  it.each(["pie", "donut", "scatter", ""])("rejects a chart type outside the allowlist (%s)", (type) => {
    const result = ChartSpecSchema.safeParse({
      type,
      title: "t",
      x: ["a"],
      y: [1],
    });
    expect(result.success).toBe(false);
  });

  it("rejects mismatched x/y lengths", () => {
    const result = ChartSpecSchema.safeParse({
      type: "bar",
      title: "t",
      x: ["a", "b"],
      y: [1],
    });
    expect(result.success).toBe(false);
  });

  it("rejects an empty data series", () => {
    const result = ChartSpecSchema.safeParse({
      type: "bar",
      title: "t",
      x: [],
      y: [],
    });
    expect(result.success).toBe(false);
  });
});
