# Part D – Computational Fluid Dynamics Toolkit

Part D tracks the roadmap for CFD exploration. While the repository stops short
of a full 3D CFD workflow, the new simulation modules provide:

* Validated 1D solvers that can seed CFD boundary conditions and benchmark
  solutions.
* Modular segment definitions (`SiphonSegment`) that map directly to meshing
  blocks or pipe-network representations in external CFD packages.
* Diagnostic outputs (Reynolds history, crest pressures, loss coefficients) that
  identify when more sophisticated CFD tools are required.

Future work will involve coupling these solvers to volumetric meshing and
post-processing utilities, but the computational framework and documentation are
now aligned so that the transition to full CFD is well specified.
