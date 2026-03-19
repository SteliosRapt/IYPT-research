# Physics Model

## Problem framing

- Fixed walls only. No moving rigid bodies, no FSI, no moving mesh.
- Two-phase incompressible, isothermal, immiscible water/air baseline.
- Container is open-top and the tube interior is part of the fluid domain.
- The steady-state detector arms only after the first upward crossing of `h0`.

## Initialization

- Initial container height uses `H(0) = 4 * h2 / 5`.
- Water occupies the container footprint below that height.
- Air occupies the rest of the domain in the MVP implementation.

## Forcing modes

- `none`
- `inflow_patch`
- `volumetric_source`
- `reservoir_head`

The current default is `inflow_patch`, because it is explicit, simple to parameterize, and maps directly onto a boundary condition.

## Measurements

- `H(t) = water_volume_in_container_region / A_plan`
- `Q_out(t)` from the tube outlet patch
- cumulative discharged volume from integrating `Q_out`
- event times `t_h0_up` and `t_steady`

## State machine

- `PRE_H0`
- `POST_H0_MONITORING`
- `DONE`

The implementation uses rolling-window span and RMS derivative thresholds, with an optional `Q_in - Q_out` balance check and dwell time.

