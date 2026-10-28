# Part A – Foundational Fluid Mechanics

Part A captures the theoretical groundwork required for the siphon project. The
content in `docs/Comprehensive_Siphon_Physics_Framework.md` now covers the
complete checklist from continuity and momentum conservation through surface
tension, cavitation, and the key dimensionless groups. Readers can treat this as
the canonical reference when building or validating the models in later parts.

* **Continuity & Navier–Stokes:** Fully derived with physical intuition and
  links to how the simulation code applies the equations.
* **Energy relations:** Bernoulli, hydrostatics, and the role of losses are all
  derived and tied to the numerical solvers.
* **Material behaviour:** Newtonian fluid assumptions, viscosity measurement,
  and limitations are documented and cross-referenced throughout the docs.
* **Dimensionless diagnostics:** Reynolds, Froude, and Weber numbers are
  defined, interpreted, and used to guide solver configuration and stability
  checks.

With these notes completed, Part A acts as a self-contained primer that matches
the rigour demanded in `Attempt/musthaves.md` while pointing directly to the
implementations that rely on each result.
