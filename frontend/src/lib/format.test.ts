import { describe, expect, it } from "vitest";

import { EXPERIENCE_LEVEL_LABELS, formatCurrency, labelFor, remoteRatioLabel } from "./format";

describe("formatCurrency", () => {
  it("formats a number as whole-dollar USD", () => {
    expect(formatCurrency(128500)).toBe("$128,500");
  });

  it("rounds off cents", () => {
    expect(formatCurrency(99999.9)).toBe("$100,000");
  });
});

describe("remoteRatioLabel", () => {
  it.each([
    [0, "On-site"],
    [50, "Hybrid"],
    [100, "Remote"],
  ])("maps %s to %s", (value, expected) => {
    expect(remoteRatioLabel(value)).toBe(expected);
  });

  it("falls back to a generic label for an unexpected value instead of mislabeling it", () => {
    expect(remoteRatioLabel(25)).toBe("25% remote");
  });
});

describe("labelFor", () => {
  it("returns the human label for a known code", () => {
    expect(labelFor(EXPERIENCE_LEVEL_LABELS, "SE")).toBe("Senior-level");
  });

  it("falls back to the raw code for an unknown value rather than throwing", () => {
    expect(labelFor(EXPERIENCE_LEVEL_LABELS, "ZZ")).toBe("ZZ");
  });
});
