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
