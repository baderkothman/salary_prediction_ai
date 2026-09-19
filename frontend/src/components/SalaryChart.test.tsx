import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InvalidChartFallback, SalaryChart } from "./SalaryChart";
import type { ChartSpec } from "../lib/schemas";

const spec: ChartSpec = {
  type: "bar",
  title: "Median salary by experience level",
  x: ["Entry-level", "Senior-level"],
  y: [56000, 140000],
};

describe("SalaryChart", () => {
  it("renders the chart title", () => {
    render(<SalaryChart spec={spec} />);
    expect(screen.getByText("Median salary by experience level")).toBeInTheDocument();
  });

  it("renders an accessible text summary of every data point (recharts' SVG isn't reliably testable in jsdom)", () => {
    render(<SalaryChart spec={spec} />);
    const summary = screen.getByText(/Entry-level \$56,000, Senior-level \$140,000/);
    expect(summary).toBeInTheDocument();
  });
});

describe("InvalidChartFallback", () => {
  it("renders a fallback message instead of crashing on bad chart data", () => {
    render(<InvalidChartFallback />);
    expect(screen.getByText(/couldn't be displayed/)).toBeInTheDocument();
  });
});
