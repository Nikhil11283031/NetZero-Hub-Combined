> Retained from the earlier standalone EPA package. Its setup, authentication and integration status describe that version. For the combined project, use ../../README.md and ../../docs/INTEGRATION.md.

# Implementation update — version 2

The package includes a React frontend connected to the two FastAPI services. The report alignment on 15 October 2026 incorporates this frontend, the shared-portal contract, the recorded checks and updated architecture/deployment diagrams. The notes below describe the implementation and the report changes.

## What changed

- React/Vite/React Router UI with applicant and officer demo workspaces.
- Dashboard, case filters, application/variation/incident forms, licence cards, status views and activity timelines.
- State-aware actions for missing information, assessments, decisions, triage, evidence, licence-context review and case conclusion.
- Reusable EPA feature module and embedded layout for the group's shared portal.
- Owner-filtered case/licence lists, authorised case histories, live CSV/XES exports and stricter command validation in the backend.
- Real event-based activity statistics, with session timings clearly separated from simulated business-hour analysis.
- Optional Compose deployment containing the two API services and an Nginx/React web container.
- Local launcher, dependency lockfile, API tests, frontend tests and automated browser workflows.

## Part E coverage

Part E explains the two business capabilities, separate databases, React pages, shared fetch client, state-aware actions, versioned commands and reusable portal module. Verification evidence is recorded in `docs/VERIFICATION.md`.

The React UI calls same-origin prefixed API routes. Vite handles them during development and Nginx is configured to handle them in Compose. The incident service retrieves licence context using backend-to-backend HTTP, and the browser workflow verifies the licence changes are visible after a variation.

## Architecture and deployment

The application-layer view includes the React EPA module consuming both APIs. The deployment view shows the browser, web delivery/proxy, two backends and separate databases. Docker remains an optional configured route whose execution has not been verified.

## Honest implementation limits

- Demo accounts are published role fixtures, not signup/password/JWT authentication.
- Document references and evidence summaries are text; file-byte uploads are not implemented.
- The frontend activity view computes counts, observed variants and elapsed session times. Mining itself remains in the Python workflow/tooling.
- The report and architecture/deployment diagrams were updated during the documentation alignment; changes to the implementation still require corresponding documentation review.
- Other providers and the group's final authentication/router configuration are outside this EPA source package.
