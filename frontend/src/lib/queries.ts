import { useQuery } from "@tanstack/react-query";

import { supabase } from "./supabase";
import { PipelineRunSchema, SalaryResultSchema, type SalaryResult } from "./schemas";
import { groupMedianBy, median } from "./stats";

export interface ResultFilters {
  experienceLevel?: string;
  employmentType?: string;
  companySize?: string;
  remoteRatio?: number;
  jobTitle?: string;
}

export const PAGE_SIZE = 20;

export function useLatestPublishedRun() {
  return useQuery({
    queryKey: ["latest-published-run"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("pipeline_runs")
        .select("*")
        .eq("status", "published")
        .order("published_at", { ascending: false })
        .limit(1)
        .maybeSingle();

      if (error) throw error;
      if (!data) return null;
      return PipelineRunSchema.parse(data);
    },
  });
}

export function useSalaryResults(runId: string | undefined, filters: ResultFilters, page: number) {
  return useQuery({
    queryKey: ["salary-results", runId, filters, page],
    enabled: Boolean(runId),
    queryFn: async () => {
      let query = supabase
        .from("salary_results")
        .select("*", { count: "exact" })
        .eq("run_id", runId as string);

      if (filters.experienceLevel) query = query.eq("experience_level", filters.experienceLevel);
      if (filters.employmentType) query = query.eq("employment_type", filters.employmentType);
      if (filters.companySize) query = query.eq("company_size", filters.companySize);
      if (filters.remoteRatio !== undefined) query = query.eq("remote_ratio", filters.remoteRatio);
      if (filters.jobTitle) query = query.eq("job_title", filters.jobTitle);

      const from = page * PAGE_SIZE;
      const to = from + PAGE_SIZE - 1;

      const { data, error, count } = await query
        .order("predicted_salary_usd", { ascending: false })
        .range(from, to);

      if (error) throw error;

      const rows: SalaryResult[] = (data ?? []).map((row) => SalaryResultSchema.parse(row));
      return { rows, total: count ?? 0 };
    },
  });
}

export function useSalaryResult(id: string | undefined) {
  return useQuery({
    queryKey: ["salary-result", id],
    enabled: Boolean(id),
    queryFn: async () => {
      const { data, error } = await supabase.from("salary_results").select("*").eq("id", id as string).single();
      if (error) throw error;
      return SalaryResultSchema.parse(data);
    },
  });
}

export interface OverviewStats {
  count: number;
  medianSalary: number;
  minSalary: number;
  maxSalary: number;
  distinctJobTitles: number;
  byExperienceLevel: { label: string; value: number }[];
  byCompanySize: { label: string; value: number }[];
}

export function useOverviewStats(runId: string | undefined) {
  return useQuery({
    queryKey: ["overview-stats", runId],
    enabled: Boolean(runId),
    queryFn: async (): Promise<OverviewStats> => {
      const { data, error } = await supabase
        .from("salary_results")
        .select("job_title, experience_level, company_size, predicted_salary_usd")
        .eq("run_id", runId as string);

      if (error) throw error;

      const rows = data ?? [];
      const salaries = rows.map((r) => r.predicted_salary_usd as number);

      return {
        count: rows.length,
        medianSalary: median(salaries),
        minSalary: salaries.length ? Math.min(...salaries) : 0,
        maxSalary: salaries.length ? Math.max(...salaries) : 0,
        distinctJobTitles: new Set(rows.map((r) => r.job_title as string)).size,
        byExperienceLevel: groupMedianBy(rows, "experience_level", "predicted_salary_usd").sort(
          (a, b) => EXPERIENCE_ORDER.indexOf(a.label) - EXPERIENCE_ORDER.indexOf(b.label)
        ),
        byCompanySize: groupMedianBy(rows, "company_size", "predicted_salary_usd").sort(
          (a, b) => COMPANY_SIZE_ORDER.indexOf(a.label) - COMPANY_SIZE_ORDER.indexOf(b.label)
        ),
      };
    },
  });
}

const EXPERIENCE_ORDER = ["EN", "MI", "SE", "EX"];
const COMPANY_SIZE_ORDER = ["S", "M", "L"];

export interface FilterOptions {
  experienceLevels: string[];
  employmentTypes: string[];
  companySizes: string[];
  remoteRatios: number[];
  jobTitles: string[];
}

export function useFilterOptions(runId: string | undefined) {
  return useQuery({
    queryKey: ["filter-options", runId],
    enabled: Boolean(runId),
    queryFn: async (): Promise<FilterOptions> => {
      const { data, error } = await supabase
        .from("salary_results")
        .select("experience_level, employment_type, company_size, remote_ratio, job_title")
        .eq("run_id", runId as string);

      if (error) throw error;

      const rows = data ?? [];
      const uniqueSorted = <T,>(values: T[]): T[] => Array.from(new Set(values)).sort();

      return {
        experienceLevels: uniqueSorted(rows.map((r) => r.experience_level as string)),
        employmentTypes: uniqueSorted(rows.map((r) => r.employment_type as string)),
        companySizes: uniqueSorted(rows.map((r) => r.company_size as string)),
        remoteRatios: uniqueSorted(rows.map((r) => r.remote_ratio as number)),
        jobTitles: uniqueSorted(rows.map((r) => r.job_title as string)),
      };
    },
  });
}
