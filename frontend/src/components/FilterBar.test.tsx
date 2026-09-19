import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { FilterBar } from "./FilterBar";
import type { FilterOptions, ResultFilters } from "../lib/queries";

const options: FilterOptions = {
  experienceLevels: ["EN", "SE"],
  employmentTypes: ["FT"],
  companySizes: ["S", "M", "L"],
  remoteRatios: [0, 50, 100],
  jobTitles: ["Data Scientist", "Data Engineer"],
};

describe("FilterBar", () => {
  it("calls onChange with the selected experience level", async () => {
    const onChange = vi.fn();
    render(<FilterBar options={options} filters={{}} onChange={onChange} />);

    await userEvent.selectOptions(screen.getByLabelText("Experience"), "SE");

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ experienceLevel: "SE" }));
  });

  it("does not show a clear-filters button when nothing is active", () => {
    render(<FilterBar options={options} filters={{}} onChange={vi.fn()} />);
    expect(screen.queryByText("Clear filters")).not.toBeInTheDocument();
  });

  it("shows a clear-filters button once a filter is active, and clears all filters when clicked", async () => {
    const onChange = vi.fn();
    const filters: ResultFilters = { experienceLevel: "SE" };
    render(<FilterBar options={options} filters={filters} onChange={onChange} />);

    const clearButton = screen.getByText("Clear filters");
    expect(clearButton).toBeInTheDocument();

    await userEvent.click(clearButton);
    expect(onChange).toHaveBeenCalledWith({});
  });

  it("clears the filter back to undefined when 'All levels' is reselected", async () => {
    const onChange = vi.fn();
    render(<FilterBar options={options} filters={{ experienceLevel: "SE" }} onChange={onChange} />);

    await userEvent.selectOptions(screen.getByLabelText("Experience"), "");

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ experienceLevel: undefined }));
  });
});
