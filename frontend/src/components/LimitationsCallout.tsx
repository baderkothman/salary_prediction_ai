export function LimitationsCallout({ limitations }: { limitations: string[] }) {
  if (limitations.length === 0) return null;

  return (
    <aside className="limitations-callout" role="note">
      <span className="limitations-callout__title">Limitations</span>
      <ul>
        {limitations.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </aside>
  );
}
