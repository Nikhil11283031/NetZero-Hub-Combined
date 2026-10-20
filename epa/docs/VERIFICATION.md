> Retained from the earlier standalone EPA package. Its setup, authentication and integration status describe that version. For the combined project, use ../../README.md and ../../docs/INTEGRATION.md.

# Verification record — full-stack version 2

Verified on 9 October 2026 in a Linux environment using Python 3.12 and Node.js 24.19.0. These are checks of the university prototype, not of a real NSW EPA system.

| Check | Result | Evidence |
|---|---|---|
| Python API and domain tests | 19 passed | `results/api_v2_tests.txt`; `tests/test_api.py`, `tests/test_frontend_api.py` |
| JavaScript API-client and analysis helpers | 7 passed | `frontend/tests/api.test.js`, `frontend/tests/model.test.js` |
| React production build | Passed | Vite compiled 34 modules; built output included in `frontend/dist/` |
| Live HTTP service composition | Passed | `results/http_demo.json` records approved application/variation, concluded incident and licence context version 2 |
| Browser workflows | All 6 passed individually | `results/frontend_browser_tests.txt`; `frontend/tests/workflows.spec.js` |
| Mobile dashboard overflow regression | Passed after correction | Dashboard and incident form fit a 390 px viewport; updated mobile screenshot |
| Compose configuration | YAML parsed; containers not executed | `compose.yaml` and supplied Dockerfiles |

## Browser coverage

1. Applicant submits an incomplete application; officer requests information; applicant supplies it; officer records both assessments and approves. A variation is then approved, and an incident investigation retrieves the updated licence through actual backend HTTP before conclusion. No page JavaScript errors were observed in this flow.
2. A different applicant cannot list/read another applicant's case or event history.
3. A concurrent update causes a stale-version error; refreshing restores the correct available actions.
4. A double click creates one case; a failed assessment offers refusal rather than approval.
5. The officer downloads actual CSV and XES event files.
6. The mobile dashboard and incident form fit their viewport; a simulated service outage produces a readable error.

The mobile visual review found an absolutely positioned accessibility label extending beyond the case table's scroll area. The table's scroll wrapper now contains positioned children. The mobile test was strengthened and passed again after this change; the production build was rerun successfully. Horizontal scrolling remains intentional inside a wide case table and the compact mobile navigation.

## Browser runtime details

The standard Playwright browser download was unavailable in this execution environment. Verification used a separately provisioned Chromium 153 binary through the optional `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` setting. This serverless binary could not reliably reuse browser contexts, so each of the six tests ran in its own Playwright invocation. All six passed individually; a single combined run with a standard Playwright Chromium installation was not executed here.

For a normal development machine, install the supported Playwright browser with `npx playwright install chromium` and run `npm run test:e2e`. The custom binary setting is optional and is not required to run the application.

## Visual evidence

- `results/frontend/dashboard-desktop.png`
- `results/frontend/incident-workflow.png`
- `results/frontend/dashboard-mobile.png`

These are screenshots of the running React application using synthetic test cases. Case counts and references depend on the local test database; a fresh application starts with no cases.

## Remaining validation at group integration

Docker Engine and Nginx were not available for execution. The optional container configuration therefore needs a group-machine `docker compose up --build` check. Windows and macOS startup instructions were supplied but were not executed on those operating systems.

The shared group portal, its authentication provider and other providers' services were not present in this package. Verify their integration using `docs/GROUP_INTEGRATION.md`. The published demo tokens, text-only document references and synthetic decisions are deliberate prototype limits.

This report alignment updated the implementation description, service-ID presentation and architecture/deployment views. The seeded results and application source were retained. The documentation revision reused the recorded verification above and did not rerun the application tests.
