# Integration verification

The combined source was built and exercised with the real Django and two FastAPI processes. The local check used isolated SQLite databases for all three APIs and the Vite development proxy. The supplied Docker setup uses MySQL for Django and nginx for the frontend.

## Completed checks

| Check | Result |
| --- | --- |
| Django recycling, solar and EPA identity tests | 34 passed |
| EPA domain, read API and shared identity tests | 27 passed |
| EPA frontend helper tests | 7 passed |
| Environment helper preserves configured passwords and is repeatable | 1 passed |
| Browser and real HTTP integration scenarios | 2 passed |
| Vite production build | Passed |
| Compose YAML structure, six services, build contexts, dependency names and volumes | Checked |
| `git diff --check` | Passed |

The browser check signs in through the group login, verifies the green leaf and both dashboard links, submits an EPA application, refreshes an EPA deep link, checks the dashboard count, visits recycling and solar, and checks EPA navigation at 1440px and 390px widths. Screenshots were inspected for layout. No browser page errors were observed.

The real HTTP integration check completes:

1. P1 application checks, assessments and approval.
2. P2 variation approval, updating the same licence to version 2.
3. P3 incident investigation, retrieving version 2 from the licensing service over HTTP and recording an outcome.

It also checks case ownership, officer-only commands, resistance to role assignment during registration, CSV/XES exports, token revocation after logout and rejection of old standalone demo tokens. Unit tests additionally cover identity-service outages and the limited internal-service credential.

## Deployment limitation

Docker and nginx were not available in the verification environment. The actual Compose images, MySQL container and nginx routing have therefore **not been executed here**. The YAML and routing configuration were inspected, and the equivalent application paths were tested through Vite. Running the supplied Compose stack on Windows remains the deployment check; the source is not presented as a completed Docker run.

After startup on your PC, use:

```powershell
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 backend epa-licensing epa-incidents frontend
```

Confirm the backend and both EPA APIs are healthy, then sign in at http://localhost:3000/login and click both Environment Protection buttons. The root README covers preserving the existing group database.

## Repeating tests

With the appropriate Python requirements installed, run `python manage.py test recycling solar` from `backend/`, and `python -m unittest tests.test_api tests.test_frontend_api tests.test_portal -v` from `epa/`. Run `python -m unittest discover -s tests -p test_setup_env.py -v` from the project root.

Frontend helper tests and the production build run from `frontend/`:

```powershell
npm.cmd ci
npm.cmd run test:epa
npm.cmd run build
```

The browser tests **create demonstration accounts and records**. Run them against a disposable local test installation with the demo users seeded:

```powershell
cd frontend
npx.cmd playwright install chromium
$env:TEST_BASE_URL = "http://localhost:3000"
$env:TEST_RESIDENT_PASSWORD = "Resident927!Local"
$env:TEST_OFFICER_PASSWORD = "Provider927!Local"
npm.cmd run test:browser
```

Use the actual local demo passwords if you configured different ones. Browser tests do not start Docker automatically. They are optional verification tools, not required to run the website.

## Source baseline

The supplied group baseline corresponds to commit `7b9d01caa8e4aec5dc3407ad3407e6f0bc409824` of `SanjidaIshita/NetZero-Hub`. This package adds the EPA module and shared integration to that baseline. It does not include later remote commits or unshared edits on a group member's PC. No changes were pushed to GitHub.
