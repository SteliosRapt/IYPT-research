# Case Format

## `case.schema.json`

- `schemaVersion`
- `caseId`
- `displayName`
- `parameters`
- `derived`
- `geometry`
- `meshing`
- `transport`
- `solver`
- `forcing`
- `eventThresholds`
- `outputs`
- `runStatus`
- `provenance`

`runStatus.state` canonical values:
- `not_started`
- `generated`
- `running`
- `done`
- `failed`

## `run-manifest.schema.json`

- `schemaVersion`
- `caseId`
- `displayName`
- `timeSteps`
- `chartSeries`
- `geometryAssets`
- `fluidAssets`
- `events`
- `status`
- `paraview`
- `metadata`

`status` canonical values:
- `mock`
- `running`
- `done`
- `failed`

## Current example files

- `examples/default-case.json`
- `examples/default-openfoam-case/`
- `examples/default-mock/manifest.json`

