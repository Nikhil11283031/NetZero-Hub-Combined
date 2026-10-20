> Retained from the earlier standalone EPA package. Its setup, authentication and integration status describe that version. For the combined project, use ../../README.md and ../../docs/INTEGRATION.md.

# NetZero Hub — NSW EPA full-stack contribution

**Version 2 includes the React frontend.** This is the complete source for your one-provider, two-service contribution, ready to run locally and adapt into the group's shared React application.

| Layer | Implementation |
|---|---|
| Frontend | React 19, Vite 8, React Router 7, JavaScript, Bootstrap CSS and scoped EPA styling |
| Backend | Two independently running Python/FastAPI services |
| Storage | One SQLite database owned by each backend |
| Integration | JSON/HTTP; incident investigation retrieves licence context from licensing |
| Deployment | Local Python + Node, or optional Docker Compose with an Nginx web container |
| Analytics | Live activity view and CSV/XES exports; existing seeded simulator and PM4Py scripts retained |

This is a university demonstration. It makes no real EPA submissions, processes no payments and makes no legal decisions. Use synthetic information. Demo accounts use published bearer tokens; they are not a production authentication system. Document references are text, not uploaded files.

## 1. Install dependencies once

Install **Python 3.12** and **Node.js 24 LTS**. Open a terminal in the extracted `NSW_EPA_NetZero` folder (the folder containing this README and `run.py`).

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
cd frontend
npm.cmd ci
cd ..
.\.venv\Scripts\python.exe run.py --with-frontend
```

The explicit Python path avoids needing to change PowerShell's script execution policy.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-api.txt
cd frontend
npm ci
cd ..
.venv/bin/python run.py --with-frontend
```

Open **http://127.0.0.1:5173**. Select an applicant or officer demo account. The launcher runs the two backends and Vite. Ctrl+C stops them. Your data persists under `data/`.

If you prefer separate terminals, run `python run.py` using the virtual environment for the APIs, and `npm run dev` in `frontend/` for React. The browser still opens port 5173.

## 2. What you can do in the frontend

- Choose the applicant/reporter, officer or second-applicant demonstration account.
- View the dashboard, search/filter cases and inspect activity histories.
- Submit an application; handle a missing-information request; record both assessments; approve/refuse it.
- View issued licences; submit, assess and decide a licence variation.
- Submit an incident; triage it; collect an evidence summary; retrieve current licence context; conclude the investigation.
- Demonstrate emergency-guidance and referral branches, or close an incomplete application after its information timer expires.
- Inspect live process counts, elapsed completion times and observed task-sequence variants.
- Download officer-only CSV/XES event logs.
- Use the same pages on desktop or mobile, with loading, error and empty states.

The dashboard initially has zero cases. Submit a case yourself, or run `python demo.py` while the APIs are running to generate a synthetic completed application, variation and incident. Refresh the browser afterward. `demo.py` writes `results/http_demo.json`.

### Try the complete workflow

1. Choose **Applicant / reporter**. Open **Apply for a licence**, fill applicant/premises/activity and submit. Leave supporting references empty to try the information loop.
2. Copy the case URL. Choose **Switch demo account**, enter as **EPA officer**, and reopen that case from Case workspace.
3. Click **Check completeness**. If references are missing, the case moves to Information needed.
4. Switch to the applicant, open the case, supply document/fee/consent references and send the information.
5. Switch to the officer, check completeness again, record environmental and suitability assessments, and approve the application with a rationale. Both assessments must pass for approval.
6. Switch to the applicant. Open **Licences**, choose **Request variation**, provide replacement conditions and a reason.
7. As officer, verify eligibility, assess the variation and approve it. The licence version increases.
8. As applicant, submit an incident with the licence reference.
9. As officer, record a non-emergency/in-jurisdiction triage, collect evidence, review licence context and conclude. The context review shows the updated licence version retrieved over HTTP.
10. Open **Process activity** as officer and export the live log.

## 3. Application and API routes

| Public browser route | Screen |
|---|---|
| `/demo-access` | Demo account selector |
| `/epa` | Dashboard |
| `/epa/cases` | Accessible case list |
| `/epa/cases/licensing/{id}` | Application/variation detail and actions |
| `/epa/cases/incidents/{id}` | Incident detail and actions |
| `/epa/licences` | Issued licences and conditions |
| `/epa/licensing/applications/new` | Application form |
| `/epa/licensing/variations/new` | Variation form |
| `/epa/incidents/new` | Incident form |
| `/epa/analytics` | Officer activity and export screen |

Browser API prefixes are `/api/v1/epa/licensing` and `/api/v1/epa/incidents`. Vite/Nginx strips the prefix before forwarding to the relevant backend. Service-internal endpoints retain `/applications`, `/variations`, `/incidents`, `/cases`, etc.

Using `run.py --with-frontend`, API documentation is available at:

- http://127.0.0.1:5173/api/v1/epa/licensing/docs
- http://127.0.0.1:5173/api/v1/epa/incidents/docs

Using backend-only `python run.py`, documentation is on ports 8001 and 8002 at `/docs`.

Every creation POST sends an `Idempotency-Key`. The frontend reuses the key for an unchanged payload after a failed request and blocks duplicate clicks. Commands carry `expected_version`; the server rejects stale updates with HTTP 409. Refresh a stale case before trying again.

## 4. Optional Docker startup

With Docker Desktop/Engine and Compose available:

```bash
docker compose up --build
```

Open **http://127.0.0.1:8080**. Stop with Ctrl+C, then `docker compose down` if needed. Named volumes keep each service's database. `docker compose down` does not erase saved cases. The web port is bound to localhost for this demonstration.

Compose runs:

- `licensing`: FastAPI, internal port 8001, private licence database volume.
- `incidents`: FastAPI, internal port 8002, private incident database volume.
- `web`: compiled React files and Nginx, public localhost port 8080.

The incident service calls `http://licensing:8001` on the Compose network. Browser requests use the same origin as the web app. A browser must not call Docker-only service names.

**Docker/Nginx containers were not executed in this environment.** Local Python/Node verification is recorded in `docs/VERIFICATION.md`.

## 5. Tests and build

From the project root, using the virtual-environment Python:

```bash
python -m unittest tests.test_api tests.test_frontend_api -v
python -m tests.http_integration
```

From `frontend/`:

```bash
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Stop your normal servers before the browser test: it starts its own backends and Vite on ports 8001, 8002 and 5173 and stores test data in a separate temporary directory. Ensure `python3` (macOS/Linux) or `python` (Windows) resolves to your virtual environment, or set the `PYTHON` environment variable to the virtual-environment executable. Install Playwright's browser system dependencies if your Linux distribution requires them.

`npm run preview` serves the built frontend on http://127.0.0.1:4173; keep the backends running. The production Compose setup uses Nginx, not Vite preview.

## 6. Group integration

Read **`docs/GROUP_INTEGRATION.md`** before copying files. Import the EPA feature module into the shared React router and use `<EpaRoutes embedded />` to reuse the group's existing header/login. Do not create a second BrowserRouter.

The runnable demo uses its own shell only so you can develop and test your contribution independently. The feature pages and API client are reusable. Shared identity still needs coordination: the group's real tokens must be verified by the backends, rather than merely passed into the frontend.

## 7. Source map

| Location | Purpose |
|---|---|
| `frontend/src/App.jsx` | Standalone development host and demo account selector |
| `frontend/src/features/epa/EpaRoutes.jsx` | Reusable routes, full/embedded layout |
| `frontend/src/features/epa/context.jsx` | Receives the group's identity, URLs and mount path |
| `frontend/src/features/epa/api.js` | Requests, bearer headers, idempotency, error translation |
| `frontend/src/features/epa/forms.jsx` | Application, variation and incident forms |
| `frontend/src/features/epa/CaseDetail.jsx` | Details, history and state-dependent officer/applicant actions |
| `frontend/src/features/epa/pages.jsx` | Dashboard, case list, licences and live analytics |
| `frontend/src/features/epa/epa.css` | EPA styles scoped beneath `.epa-app` |
| `frontend/src/components/ui.jsx` | Shared display/form components |
| `services/licensing.py`, `services/incidents.py` | FastAPI endpoints and service composition |
| `services/domain.py` | Business transitions shared with the simulator |
| `services/common.py` | Storage, transactions, versioning, ownership and demo identity |
| `services/validation.py` | Typed HTTP command payload validation |
| `services/read_api.py` | Lists, case history and CSV/XES export |
| `tests/`, `frontend/tests/` | API, frontend helper and real browser tests |
| `frontend/nginx.conf`, Dockerfiles, `compose.yaml` | Optional deployment configuration |
| `models/`, `diagrams/` | Original A–D models and figures |
| `analytics/`, `results/` | Original simulator/mining code and analytical evidence |

## 8. Existing report and process mining

The DOCX/PDF now describe the React module, shared-portal integration, current recorded verification and updated architecture/deployment views. Parts A–G retain the original EPA workflows and seeded process-mining results. The report separates verified local execution from pending group authentication and Docker integration.

To rerun the existing simulated analysis, use a separate environment if preferred:

```bash
python -m pip install -r requirements.txt
python -m analytics.simulate --cases 100 --seed 927
python -m analytics.mine
```

The original seeded result has 300 simulated cases and 2,116 events. Those virtual business-hour timings are distinct from the live UI session events. The frontend does not implement a mining algorithm in the browser; export logs for mining, and use the Python PM4Py workflow for the supplied analysis.

## 9. Troubleshooting

- **Cannot reach the service:** start both APIs; check ports 8001/8002, Vite's proxy targets and browser errors.
- **Demo account rejected:** use the default published tokens consistently, or update the backend `NZ_*_TOKEN` variables and frontend demo variables together.
- **Stale version:** refresh the case and inspect the latest history; do not retry an old decision blindly.
- **No licence available:** approve an application first. Applicants see only their own licences.
- **Blank page on a deep-link refresh:** use Vite or the provided Nginx SPA fallback, not a raw static file server.
- **No browser test binary:** run `npx playwright install chromium`; the app itself does not need Playwright to run.
- **Port already occupied:** stop the previous app/test process. The development server deliberately fails rather than silently switching ports.

The complete group still needs other providers and at least one additional implemented business service. This package supplies your EPA contribution, not other members' code.
