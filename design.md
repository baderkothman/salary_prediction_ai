# Salary Prediction Application - Design Specification

## 1. Design Direction

The React website should feel like a focused **data product**, not a generic admin template.

Visual goals:

- Clear hierarchy.
- Dense enough for analysis, but not cluttered.
- Calm neutral surfaces with one primary accent.
- Strong typography for salary values and chart titles.
- Minimal decoration.
- Consistent spacing and border radii.
- Excellent desktop use with intentional responsive behavior.

Avoid:

- Excessive gradients.
- Glassmorphism.
- Decorative AI-style glow effects.
- Too many colors.
- Giant empty hero sections.
- Cards around every small text block.

---

## 2. Information Architecture

Recommended routes:

```text
/                  Overview
/explore           Explore Predictions
/results/:id       Prediction Detail
/methodology       Methodology
```

If time is limited, `/results/:id` may be implemented as a side panel from `/explore`, but the URL should remain shareable if practical.

---

## 3. Layout

### Desktop

- Maximum content width: `1440px`.
- Main horizontal page padding: `32px` to `48px`.
- Top navigation height: approximately `64px`.
- Dashboard grid: 12 columns.
- KPI cards: 4 across when width permits.
- Main chart: 8 columns.
- Secondary insight panel: 4 columns.

### Tablet

- Page padding: `24px`.
- KPI cards: 2 per row.
- Main chart + insight panel stack vertically.

### Mobile

- Page padding: `16px`.
- KPI cards: single column or 2 compact cards per row if readable.
- Filter controls collapse into a filter drawer/sheet.
- Tables may use horizontal scrolling only as a last resort; prioritize a compact card/list representation for narrow screens.

---

## 4. Design Tokens

Start with these semantic tokens. Exact values can be adjusted after implementation, but do not bypass the token layer with arbitrary component colors.

```css
:root {
  --background: #f7f8fa;
  --surface: #ffffff;
  --surface-subtle: #f1f3f5;
  --text-primary: #15191e;
  --text-secondary: #5f6975;
  --border: #dde2e7;

  --primary: #173f6b;
  --primary-strong: #103354;
  --primary-soft: #e8f0f7;

  --positive: #1f7a4d;
  --warning: #9a6700;
  --negative: #b42318;

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
}
```

Use semantic color names in components. Do not hardcode data-category colors throughout the application.

---

## 5. Typography

Use a modern, highly readable sans-serif available through the application's normal web-font strategy or system stack.

Recommended fallback stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Type scale:

| Role | Suggested size | Weight |
|---|---:|---:|
| Page title | 32-40px | 650-700 |
| Section title | 22-28px | 600-650 |
| Card metric | 28-36px | 650-700 |
| Body | 15-16px | 400 |
| Small/meta | 12-14px | 450-500 |

Use tabular numerals for salary values where available.

---

## 6. Global Navigation

Header contents:

```text
SalaryScope                 Overview  Explore  Methodology      Model vX
```

`SalaryScope` is a working product name and can be changed.

Navigation behavior:

- Sticky or static header are both acceptable; prefer sticky only if it improves exploration.
- Active route is visibly distinct.
- Model version is a small metadata chip, not a CTA.
- No unnecessary hamburger on desktop.

---

## 7. Overview Page

### Header block

Contents:

- `Salary Prediction Landscape`
- Short one-line description.
- `Last generated <date>`.
- Model version.

Do not create a large marketing hero.

### KPI cards

Show four useful metrics from the latest published run, for example:

1. Number of generated predictions.
2. Median predicted salary.
3. Lowest / highest predicted salary.
4. Number of job titles represented.

Every metric needs a clear label and, where relevant, supporting context.

### Primary chart

Default visualization:

- Median or average predicted salary by experience level.

Use a horizontal or vertical bar chart depending on label length.

### Secondary insight

Show a concise generated insight from the latest run or an aggregate narrative.

Do not make the LLM text visually dominate the page.

### Distribution / secondary chart

Display one useful secondary exploration such as:

- Salary by company size.
- Salary by remote ratio.
- Top job titles by median prediction, subject to minimum sample count.

---

## 8. Explore Page

### Filter bar

Filters should be driven by values present in the published data:

- Experience level.
- Employment type.
- Job title.
- Company size.
- Remote ratio.
- Company location if present.
- Employee residence if present.

Rules:

- Use human-friendly labels.
- Provide a visible `Clear filters` action only when filters are active.
- Do not preload hundreds of job-title options into an unusable select; use searchable combobox behavior.
- Show active filters as removable chips when useful.

### Results summary

Show:

```text
124 matching predictions · Median $118,400
```

### Results table

Recommended columns:

- Job title
- Experience
- Employment
- Company size
- Remote
- Predicted salary
- Action/details

Use server-side/Supabase pagination for large result sets.

Salary is right-aligned and formatted as currency.

### Empty result state

Text example:

```text
No predictions match these filters.
Try removing one or more filters.
```

Do not present this as an error.

---

## 9. Prediction Detail

Header:

```text
Data Scientist
Senior · Full-time · Medium company · Remote

$128,500 predicted salary
```

Sections:

### A. Prediction context

Display model input values in a compact definition-list/grid.

### B. Analyst narrative

- Headline.
- Short summary.
- 2-4 key insights.

### C. Generated chart

Render only after `chart_spec` passes runtime validation.

If chart data is invalid, show a small fallback message without breaking the rest of the page.

### D. Supporting statistics

Show the exact deterministic numbers used to ground the narrative, such as:

- Peer median.
- Peer mean.
- Sample size.
- IQR or percentile if computed.

### E. Limitations

Keep limitations visible but concise.

---

## 10. Methodology Page

Purpose: make the project understandable and reviewable.

Sections:

1. Dataset source.
2. Cleaning approach.
3. Feature set.
4. Decision Tree model.
5. Evaluation metrics.
6. How input combinations are covered.
7. How the local LLM is grounded.
8. Why the dashboard uses pre-generated results.
9. Model and dataset limitations.

This page should favor explanatory prose over decorative cards.

---

## 11. Chart Design Rules

Use Recharts.

Chart rules:

- Always show a title.
- Label axes when meaning is not obvious.
- Currency tooltips use USD formatting.
- Avoid 3D charts.
- Avoid pie/donut charts for high-cardinality comparisons.
- Avoid more than 8-10 categorical bars without scrolling or a top-N strategy.
- Sort comparison bars when order is meaningful.
- Do not use color alone to communicate state.
- Keep gridlines subtle.
- Provide a text description or supporting summary for accessibility.

LLM chart types must map to an allowlist:

```ts
type ChartType = 'bar' | 'horizontal_bar' | 'line';
```

Do not dynamically execute chart component names from database content.

---

## 12. Components

Suggested reusable components:

```text
AppHeader
PageContainer
PageHeader
MetricCard
ModelVersionBadge
FilterBar
SearchableFilter
ActiveFilterChip
SalaryChart
ChartCard
ResultsTable
ResultsMobileList
SalaryValue
InsightPanel
PredictionContextGrid
NarrativeSection
LimitationsCallout
LoadingSkeleton
EmptyState
ErrorState
```

Keep components focused. Do not create one 800-line dashboard component.

---

## 13. Loading States

Use skeletons for:

- KPI cards.
- Chart panels.
- Table rows.

Avoid a full-screen spinner after the initial shell has rendered.

---

## 14. Error States

Differentiate:

- Supabase/network error.
- No published pipeline run.
- No matching filter results.
- Invalid stored chart specification.

Example no-published-run state:

```text
No published salary dataset is available yet.
Run the generation pipeline and publish a completed run.
```

---

## 15. Accessibility

Target WCAG 2.1 AA practices.

Required:

- Keyboard-accessible navigation and filters.
- Visible focus state.
- Proper semantic headings.
- Form labels.
- Sufficient text/background contrast.
- Charts accompanied by text summaries or tabular equivalents where practical.
- `aria-live` only for meaningful async status changes.
- Do not rely on placeholder text as a label.

---

## 16. Responsive Behavior

Breakpoints may follow the styling framework, but verify at least:

- 360px
- 390px
- 768px
- 1024px
- 1440px

At 360-390px:

- No clipped header.
- Salary values do not overflow cards.
- Filters remain usable.
- Chart labels remain readable or use a scroll/container strategy.
- Detail content becomes single column.

---

## 17. Data Formatting

Currency:

```ts
new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
}).format(value)
```

Dates:

- Render human-friendly date/time in the user's browser locale.
- Store timestamps as UTC in the database.

Remote ratio labels:

```text
0   -> On-site
50  -> Hybrid
100 -> Remote
```

Only use this mapping if those are the actual dataset values.

---

## 18. Design Acceptance Checklist

- [ ] Overview is useful within the first viewport on desktop.
- [ ] Dashboard does not look like a default template.
- [ ] Typography hierarchy is clear.
- [ ] One primary accent dominates instead of many competing colors.
- [ ] All salary values use consistent currency formatting.
- [ ] Filters work on desktop and mobile.
- [ ] Loading, empty, and error states exist.
- [ ] Charts have titles and readable labels.
- [ ] LLM narrative never renders as unsafe HTML.
- [ ] Invalid chart specs fail gracefully.
- [ ] The interface works at 360px width.
- [ ] Keyboard navigation and visible focus states are present.
