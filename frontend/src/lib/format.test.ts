import { describe, expect, it } from "vitest";

import { EXPERIENCE_LEVEL_LABELS, countryLabel, formatCurrency, labelFor, remoteRatioLabel } from "./format";

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

describe("countryLabel", () => {
  it.each([
    ["US", "United States"],
    ["DE", "Germany"],
    ["IN", "India"],
    ["GB", "United Kingdom"],
  ])("maps ISO code %s to %s", (code, expected) => {
    expect(countryLabel(code)).toBe(expected);
  });

  it("describes a syntactically valid but unassigned region code instead of throwing", () => {
    // "ZZ" is a well-formed ISO 3166-1 alpha-2 shape but not an assigned
    // country -- Intl.DisplayNames itself resolves this to "Unknown Region"
    // rather than throwing, which is a reasonable display as-is.
    expect(countryLabel("ZZ")).toBe("Unknown Region");
  });

  it("falls back to the raw input for a malformed (non-region-shaped) code rather than throwing", () => {
    expect(countryLabel("not-a-code")).toBe("not-a-code");
  });
});
