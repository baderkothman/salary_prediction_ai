export function ErrorState({ message }: { message?: string }) {
  return (
    <div className="error-state" role="alert">
      <h3 className="error-state__title">Something went wrong loading this data</h3>
      <p className="error-state__description">
        {message ?? "Please try again in a moment. If this keeps happening, check your connection."}
      </p>
    </div>
  );
}
