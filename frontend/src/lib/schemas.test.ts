import { describe, expect, it } from "vitest";

import { ChartSpecSchema } from "./schemas";

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
