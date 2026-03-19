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

## Review Wave Handoff Procedure

- Use `code_review_report.md` as the issue source and `docs/code-review-wave-handoff.md` as the live execution tracker.
- Before starting a new wave, read the handoff doc, pick the next unchecked items, and mark the relevant wave as `in progress` in that document.
- When you finish a task, update the handoff doc in the same change with:
  - the completed checklist items
  - the files touched
  - the verification you actually ran
  - any blocker or follow-up left for the next wave
- Keep completed items in the handoff doc; do not rewrite history or collapse prior-wave notes into a summary only.
- If you change the suggested procedure itself, update this `AGENTS.md` and the handoff doc together so the next agent sees one consistent workflow.

