export function median(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
}

export function groupMedianBy<T extends Record<string, unknown>>(
  rows: T[],
  groupKey: keyof T,
  valueKey: keyof T
): { label: string; value: number }[] {
  const groups = new Map<string, number[]>();
  for (const row of rows) {
    const key = String(row[groupKey]);
    const value = Number(row[valueKey]);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(value);
  }
  return Array.from(groups.entries()).map(([label, values]) => ({ label, value: median(values) }));
}
