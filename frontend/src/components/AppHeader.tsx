import { NavLink } from "react-router-dom";

export function AppHeader({ modelVersion }: { modelVersion?: string }) {
  return (
    <header className="app-header">
      <div className="app-header__inner">
        <div className="app-header__brand-nav">
          <span className="app-header__brand">SalaryScope</span>
          <nav className="app-header__nav">
            <NavLink to="/" className="app-header__link" end>
              Overview
            </NavLink>
            <NavLink to="/explore" className="app-header__link">
              Explore
            </NavLink>
            <NavLink to="/methodology" className="app-header__link">
              Methodology
            </NavLink>
          </nav>
        </div>
        {modelVersion && <span className="badge">Model {modelVersion}</span>}
      </div>
    </header>
  );
}
