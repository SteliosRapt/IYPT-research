# Repository Instructions

- The source of truth for geometry, formulas, and constraints is still:
  - `experimental_setup.md`
  - `setup_3d (2).html`
- Do not edit those files unless the user explicitly asks to revise the source specification.
- Preserve the canonical parameter names from `packages/shared-schema` and keep the HTML-name mapping behavior intact.
- The importable Python package for viewer data is `services.viewer_data`, while the repo layout also keeps `services/viewer-data` as a documentation-facing folder.
- Prefer `python -m services.geometry.cli`, `python -m services.orchestrator.cli`, and `python -m services.viewer_data.cli` over ad hoc scripts.
- If Docker or OpenFOAM are unavailable, keep the mock-data path working and document the limitation instead of blocking the repo.
- Keep browser-facing example manifests under `/examples`, because the Vite app serves that directory as its public asset root.
- Update `docs/assumptions.md` whenever you introduce a new geometry, solver, or viewer assumption that is not explicit in the source files.

## Remediation Workflow

- Use `docs/remediation-roadmap.md` as the active issue source.
- Use `docs/code-review-wave-handoff.md` as the live execution log.
- Before starting new work, read both files and pick the next unresolved roadmap item.
- When you finish a task, update the execution log in the same change with:
  - completed work
  - files touched
  - verification actually run
  - any blocker or external follow-up still pending
- Treat `code_review_report.md`, `refactoring_proposal.md`, and `docs/refactoring-proposal.md` as historical context only.
- If you change the workflow itself, update this `AGENTS.md` and the execution log together.
