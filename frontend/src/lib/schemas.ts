import { z } from "zod";

// Chart type allowlist (design.md #11 / architecture.md #3.9): the LLM
// chooses a chart type, but we never let arbitrary stored data pick a
// component dynamically -- only these three ever render.
export const ChartTypeSchema = z.enum(["bar", "horizontal_bar", "line"]);
export type ChartType = z.infer<typeof ChartTypeSchema>;

export const ChartSpecSchema = z
  .object({
    type: ChartTypeSchema,
    title: z.string().max(200),
    x: z.array(z.string()).min(1).max(20),
    y: z.array(z.number()).min(1).max(20),
  })
  .refine((spec) => spec.x.length === spec.y.length, {
    message: "chart.x and chart.y must have the same length",
  });
export type ChartSpec = z.infer<typeof ChartSpecSchema>;

export const PipelineRunSchema = z.object({
  id: z.string(),
  status: z.enum(["building", "published", "failed"]),
  model_version: z.string(),
  dataset_hash: z.string(),
  llm_model: z.string(),
  prompt_version: z.string(),
  // Stored exactly as ml/src/training/train.py writes model_metadata.json's
  // "metrics" field (scripts/persist.py passes it straight through) --
  // both train and test splits, not just a flat test-only shape.
  model_metrics: z.object({
    train: z.object({ mae: z.number(), rmse: z.number(), r2: z.number() }),
    test: z.object({ mae: z.number(), rmse: z.number(), r2: z.number() }),
  }),
  coverage_summary: z.record(z.string(), z.unknown()).nullable().optional(),
  created_at: z.string(),
  published_at: z.string().nullable(),
});
export type PipelineRun = z.infer<typeof PipelineRunSchema>;

export const SalaryResultSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  feature_signature: z.string(),
  work_year: z.number().nullable(),
  experience_level: z.string(),
  employment_type: z.string(),
  job_title: z.string(),
  employee_residence: z.string().nullable(),
  remote_ratio: z.number().nullable(),
  company_location: z.string().nullable(),
  company_size: z.string(),
  features: z.record(z.string(), z.unknown()),
  predicted_salary_usd: z.number(),
  analysis_headline: z.string().nullable(),
  analysis_summary: z.string().nullable(),
  key_insights: z.array(z.string()).nullable(),
  chart_spec: ChartSpecSchema.nullable().catch(null),
  analysis_context: z.record(z.string(), z.unknown()).nullable(),
  limitations: z.array(z.string()).nullable(),
  created_at: z.string(),
});
export type SalaryResult = z.infer<typeof SalaryResultSchema>;
