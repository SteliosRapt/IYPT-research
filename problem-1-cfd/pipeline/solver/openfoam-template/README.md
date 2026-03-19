# OpenFOAM Template

This folder contains the Docker support and the reference runtime assumptions for the MVP solver path.

The generated cases in `/examples/default-openfoam-case` and any future case directories are created by:

`python -m services.orchestrator.cli generate-case ...`

The MVP currently writes the dictionaries directly into each case directory because the geometry-dependent values are resolved at generation time.

