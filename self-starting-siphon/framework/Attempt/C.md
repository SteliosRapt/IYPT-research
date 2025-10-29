# Part C – Self-Starting Siphons & Transients

Part C consolidates the unsteady flow analysis from
`docs/Comprehensive_Siphon_Physics_Framework.md` Sections 6–8 and the variable
loss simulator:

* The documentation walks through momentum-driven priming, transient Bernoulli
  balances, and cavitation/entrainment limits.
* `simulations/variable_losses.py` captures these dynamics numerically by
  advancing the nonlinear head/flow coupling, including regime transitions and
  crest-pressure monitoring.
* Suggested experiments and validation hooks (CSV import + regression tests) are
  outlined in `docs/physics_overview.md` to close the loop with data.

Deliverables for Part C now have both the theoretical basis and executable code
to explore self-starting behaviour.
