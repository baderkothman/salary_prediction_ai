import type { ReactNode } from "react";

export function PageContainer({ children }: { children: ReactNode }) {
  return (
    <main className="page-container">
      <div className="page-container__inner">{children}</div>
    </main>
  );
}

export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="page-header">
      <h1 className="page-header__title">{title}</h1>
      {description && <p className="page-header__description">{description}</p>}
    </div>
  );
}
