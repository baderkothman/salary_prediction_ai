// LLM narrative is always rendered as plain React text content, never
// dangerouslySetInnerHTML (security.md #10) -- React escapes it by default.
export function NarrativeSection({
  headline,
  summary,
  insights,
  comparison,
}: {
  headline: string;
  summary: string;
  insights: string[];
  comparison?: string | null;
}) {
  return (
    <section className="narrative">
      <h3 className="narrative__headline">{headline}</h3>
      <p className="narrative__summary">{summary}</p>
      {comparison && <p className="narrative__comparison">{comparison}</p>}
      {insights.length > 0 && (
        <ul className="narrative__insights">
          {insights.map((insight, i) => (
            <li key={i}>{insight}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
