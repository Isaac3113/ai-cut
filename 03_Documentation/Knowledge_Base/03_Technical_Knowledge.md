# Technical knowledge
One authoritative main timeline. Speech defaults to absolute 1.2, with per-video override. New graphics use final timing at 1.0; documented approved-asset retiming follows final-delivery.md. Background music is processed separately; never re-normalize a mix to compensate for weak raw speech. See master Skill and docs/VALIDATION.md.

2026-09-13: Keep code/runtime/work outside OneDrive; the Project Hub stores documents, media and deliveries. Directory helper requires a configured Hub and separately creates local work. Existing Chinese titles are preserved; Windows CLI output uses UTF-8. See master references/project-storage.md. Actual regression status: docs/VALIDATION.md.

## 0.2.5 current defaults and evidence
New plans use absolute 1.2x; saved historical plans are unchanged and a missing historical speed still resolves to 1x. Old 1.1x ChatCut snapshots require `--expected-speed 1.1`. The separate `schemas/visual-contract.schema.json` binds supplied-logo/evidence hashes, source-time PIP coverage, effective visible bounds and caption collision. Existing source-anchored timeline and cache algorithms are preserved. Human viewing/listening and pixel-level mask checks remain separate.
