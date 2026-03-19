import { NavLink, Route, Routes } from "react-router-dom";

import { ConfigurePage } from "@/pages/ConfigurePage";
import { RunsPage } from "@/pages/RunsPage";

export function App() {
  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Fixed Geometry CFD</p>
          <h1>Experiment configurator and run browser</h1>
        </div>
        <nav className="nav">
          <NavLink to="/" end>
            Configure
          </NavLink>
          <NavLink to="/runs">Runs</NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<ConfigurePage />} />
        <Route path="/runs" element={<RunsPage />} />
      </Routes>
    </div>
  );
}

