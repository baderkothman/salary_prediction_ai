export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="empty-state" role="status">
      <h3 className="empty-state__title">{title}</h3>
      {description && <p className="empty-state__description">{description}</p>}
    </div>
  );
}
