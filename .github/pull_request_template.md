IMPORTANT:
- PR must be opened from your personal branch → dev
- You must tag @Team-Deepiri/support-team
- You must update Plaky to "Needs QA"
- Never move a task to "Done" (Done = production release only)
- If this PR makes the dog happier, say woof. If it doesn't, still say woof — we're professionals.

---

## Description

Briefly explain what this PR does and why. What intent are we forecasting now?

Include:
- Related Issue number
- Plaky feature name
- Component, feature, or system affected (runtime, perception, pocket app, collar, etc.)
- Purpose of change (feature, bug fix, improvement, refactor, security, etc.)

---

## Changes

List the most important updates in this PR (the good stuff we fetched):

- 
- 
- 
- 

Be specific. Include:
- New or updated functions, services, components, or scripts
- Refactoring or structural improvements
- Dependency or configuration changes
- Any significant implementation details

---

## Related

- Issue:
- Plaky:
- Related PRs (optional):

---

## Testing

Explain how you verified your changes and how to test your feature. No merging on vibes alone — run the sniff test.

Additional testing details:

For **deepiri-aarflingo** changes, note if you ran:
- `poetry install` (root lock) or `poetry install -E yolo` for vision
- `make test` / `make smoke`
- `./scripts/verify_aarflingo.sh`
- `./scripts/run_runtime.sh` + studio / Electron (if runtime or UI touched)
- Pocket apps: Android debug build / iOS simulator (if mobile touched)

---

## Important Notes (Optional)

- Known limitations:
- Blockers:
- CI/CD issues unrelated to this PR:
- Dependencies required for testing:
- Did you pet a dog today? (optional but encouraged)

---

## Workflow Checklist (Required)

- [ ] Branch is up to date with dev
- [ ] PR is from your branch → dev (no longer directly into main)
- [ ] PR title follows convention (feat:, fix:, refactor:, etc.)
- [ ] Plaky feature/bug name included above
- [ ] Tagged @Team-Deepiri/support-team
- [ ] Plaky task moved to "Needs QA"
- [ ] CI is green (or you left a note why not) — good boy/girl energy only

---

## Review Requests

@Team-Deepiri/support-team

woof 🐾
