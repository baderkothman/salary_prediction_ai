const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export const EXPERIENCE_LEVEL_LABELS: Record<string, string> = {
  EN: "Entry-level",
  MI: "Mid-level",
  SE: "Senior-level",
  EX: "Executive-level",
};

export const EMPLOYMENT_TYPE_LABELS: Record<string, string> = {
  FT: "Full-time",
  PT: "Part-time",
  CT: "Contract",
  FL: "Freelance",
};

export const COMPANY_SIZE_LABELS: Record<string, string> = {
  S: "Small",
  M: "Medium",
  L: "Large",
};

// Only meaningful for this dataset's remote_ratio values (0/50/100); a
// value outside that set is shown as-is rather than mislabeled.
export function remoteRatioLabel(value: number): string {
  switch (value) {
    case 0:
      return "On-site";
    case 50:
      return "Hybrid";
    case 100:
      return "Remote";
    default:
      return `${value}% remote`;
  }
}

export function labelFor(dict: Record<string, string>, code: string): string {
  return dict[code] ?? code;
}

// ISO 3166-1 alpha-2 -> country name, via the standard Intl.DisplayNames
// Web API rather than a hand-maintained lookup table -- covers every real
// country code correctly with zero new dependencies. Falls back to the
// raw code if the runtime lacks the API or the code isn't recognized.
const regionDisplayNames =
  typeof Intl !== "undefined" && "DisplayNames" in Intl ? new Intl.DisplayNames(["en"], { type: "region" }) : null;

export function countryLabel(code: string): string {
  try {
    return regionDisplayNames?.of(code) ?? code;
  } catch {
    return code;
  }
}
