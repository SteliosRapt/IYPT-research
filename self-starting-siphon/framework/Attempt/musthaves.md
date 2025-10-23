# Siphon Physics
**scope**: Newtonian fluids, both viscuous and not. Also unstable fluid flows in the context of priming a siphon.
Complete mathematical rigor, complete intuition, everything cited and verified, proven from fundamental truths.

## A. Fundamental concepts
1. versions of continuity equation proven from conservation of mass
2. What is a newtonian fluid, Navier-Stokes Equations explained
3. Bernoulli's equation from Navier-Strokes with clear assumptions and limitations
4. Hydrostatic pressure from Navier-Strokes
5. Surface tension
6. Raynold's number and why it characterises flow type, proof, citations and what it means.
7. Mechanics of different flow types
8. Froude Number and explanation, uses
9. Weber Number

## B. Primed siphons
### B.1 No losses
1. Flow velocity from bernoulli equation (finite reservoir only)
2. Flow rate
3. Drainage time, conteiner height over time
4. Pressure distribution
5. Cavitation limit
6. model summary: equation table, assumptions, strengths and limitations
### B.2 Losses
1. Viscosity: intuition, math and effect on fluid movements, measurement methods and why they measure this exact physical quantity
2. Loss mechanisms
3. Darcy-Weisbach equation
4. Effect on losses by flow type (laminar, transition, and turbulent flow)
5. Minor losses
6. Complete siphon model with losses, equation table, assumptions, strengths and limitations
7. computational/ iterative methods

**Advanced geometries, and applying the models described.**
1. Variable cross-section (tapered tubes, expansions/contractions)
2. Multiple crests (up-down-up-down paths)
3. 3D curved paths
4. Branching (multiple inlets or outlets)
## C. self-starting siphon priming: Unsteady flows
1. transient dynamics
2. Momentum driven siphons
3. Complete model without losses
4. Model with complete losses, advanced dynamics, from priming to drainage
5. Programmatic and computational methods for Self-starting siphons
6. Suggested experiments to compare models with reality
## D. CFD using python
How to work with any geometry and initial conditions working with 3D objects and the exact pressure/ velocity fields of the fluid, how to visualise it and how to create study self-starting siphons.