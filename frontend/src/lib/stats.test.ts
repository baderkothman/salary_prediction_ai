import { describe, expect, it } from "vitest";

import { groupMedianBy, median } from "./stats";

describe("median", () => {
  it("returns the middle value for an odd-length array", () => {
    expect(median([1, 3, 2])).toBe(2);
  });

  it("averages the two middle values for an even-length array", () => {
    expect(median([1, 2, 3, 4])).toBe(2.5);
  });

  it("returns 0 for an empty array instead of NaN", () => {
    expect(median([])).toBe(0);
  });

  it("does not mutate the input array", () => {
    const input = [3, 1, 2];
    median(input);
    expect(input).toEqual([3, 1, 2]);
  });
});

describe("groupMedianBy", () => {
  it("computes the median predicted salary per group", () => {
    const rows = [
      { experience_level: "EN", predicted_salary_usd: 50000 },
      { experience_level: "EN", predicted_salary_usd: 60000 },
      { experience_level: "SE", predicted_salary_usd: 140000 },
    ];
    const result = groupMedianBy(rows, "experience_level", "predicted_salary_usd");
    expect(result).toEqual(
      expect.arrayContaining([
        { label: "EN", value: 55000 },
        { label: "SE", value: 140000 },
      ])
    );
  });
});
