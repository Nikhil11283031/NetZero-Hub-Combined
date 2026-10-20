> Retained from the earlier standalone EPA package. Its setup, authentication and integration status describe that version. For the combined project, use ../../README.md and ../../docs/INTEGRATION.md.

# Add the EPA module to the shared React application

## Frontend contract

Agree these values with the team:

| Item | Default |
|---|---|
| React route prefix | `/epa` |
| Licensing API prefix | `/api/v1/epa/licensing` |
| Incident API prefix | `/api/v1/epa/incidents` |
| Browser identity | `{ subject, name, role, token }` |
| Role values consumed by the UI | `client` or `officer` |
| Case processes | P1 application, P2 variation, P3 incident investigation |
| Business service IDs | EPA-001 and EPA-002 (UI labels EPA001 and EPA002 are aliases) |

1. Copy `frontend/src/features/epa/` and `frontend/src/components/ui.jsx`, retaining their relative folder structure (or adjust the imports deliberately).
2. Use the group's existing React/React Router packages. Reconcile versions in the shared lockfile once, rather than keeping a second app's `node_modules`.
3. Load Bootstrap CSS once in the shared application, if it is not already loaded. Import `features/epa/epa.css` after it. Do not copy the demo-host `styles.css` or `App.jsx` unless you want that host.
4. Add one route inside the group's existing router:

```jsx
import EpaRoutes from './features/epa/EpaRoutes.jsx';
import { EpaProvider } from './features/epa/context.jsx';
import './features/epa/epa.css';

// In the group's existing <Routes>. The surrounding portal owns login/navigation.
<Route
  path="/epa/*"
  element={
    <EpaProvider
      key={currentUser.subject}
      profile={{
        subject: currentUser.subject,
        name: currentUser.name,
        role: currentUser.role,
        token: accessToken,
      }}
      licensingUrl="/api/v1/epa/licensing"
      incidentsUrl="/api/v1/epa/incidents"
      basePath="/epa"
    >
      <EpaRoutes embedded />
    </EpaProvider>
  }
/>
```

The snippet assumes the group's authenticated `currentUser` and `accessToken` already exist. Render the route only after authentication resolves. Remount the provider when the user changes to avoid retaining the previous user's form state. The module itself does not create a BrowserRouter. Embedded mode omits the demo header, sidebar and account switcher and keeps local EPA navigation.

The UI's role controls are convenience only: the backend independently enforces permissions. Never make a frontend-only role change into an authorisation mechanism.

## Backend identity integration

The shipped `services.common.principal` is a deliberately simple demo adapter. It maps published tokens to fixed demo subjects. A real shared JWT will **not** work with it unchanged.

Both app factories accept `identity_dependency`, a FastAPI dependency that must return a verified principal with a stable `subject` and authorised `role`. Example entry point after the group has implemented its actual authentication:

```python
from services.licensing import create_app
from group_auth import verified_principal  # Supplied and tested by your group

app = create_app(identity_dependency=verified_principal)
```

Your verified dependency must check the group's chosen credentials/signature, issuer, audience and expiry as applicable, and map trusted claims to `client`, `officer` or the restricted `internal` service role. Do not decode a token without verifying it. Stable subjects determine record ownership.

The incident-to-licensing lookup also needs an agreed service credential. In the supplied demo this is `NZ_INTERNAL_TOKEN`, used only by the backends. If the group replaces authentication, update that exchange and the dependency together. Do not expose an internal credential as a `VITE_*` frontend variable.

## API routing

Copy the two Vite proxy rules into the group's development config and the two Nginx locations into its gateway, adjusting the backend addresses. The browser sends requests only to the public prefixes; the gateway strips them. Set each backend's `NZ_ROOT_PATH` to its public prefix so proxied API documentation works.

API origins that differ from the frontend need a deliberate CORS configuration. The provided same-origin proxy setup avoids that requirement.

Do not let another provider read or write the EPA SQLite files. Consume API operations. The incident service already demonstrates composition by reading a restricted licence-context interface over HTTP.

## Endpoint overview

Both services provide:

- `GET /health`
- `GET /me` (authenticated)
- `GET /cases` (owner-filtered; officer sees all within the service)
- `GET /cases/{case_id}`
- `GET /cases/{case_id}/events` (same ownership check)
- `POST /cases/{case_id}/commands`
- `GET /events` and `GET /events/export?format=csv|xes` (officer only)

Licensing also provides:

- `POST /applications`
- `POST /variations`
- `GET /licences`
- `GET /licences/{licence_id}`
- `GET /internal/licences/{licence_id}/context` (internal/officer only)

Incidents also provides `POST /incidents`.

Creation requires `Idempotency-Key`. A command is `{ "expected_version": 1, "action": "check", "values": {} }`. The command response includes the updated case and version. See the generated OpenAPI documents for full field schemas.

## Team handoff checks

- Confirm the shared host can open and refresh `/epa/cases/...` deep links.
- Test an applicant's case and licence ownership after integrating real identity.
- Test officer permissions and verify the internal token is not bundled into frontend assets.
- Confirm all API prefixes and response field names before other members call them.
- Agree a group-wide event identifier/case-naming convention before combining logs; retain provider identity to avoid collisions.
- Keep the original activity IDs A1–A11, V1–V8 and I1–I12 aligned with the EPA BPMN models.

## Report identifiers and event mapping

The report and model catalogue use EPA-001 and EPA-002. The current UI display labels EPA001 and EPA002 denote the same services. Local process and activity IDs are preserved. In a combined report or a separate normalised log, qualify them as EPA.P1 and EPA.P1.A1, and qualify case identifiers by provider and process. Map P1/P2 to EPA-001 and P3 to EPA-002.

Keep live API logs separate from the seeded simulation. Simulated XES uses task IDs as concept:name; live XES uses activity names and also retains task_id. Normalise the classifier before comparison. Live logs record completion times, not the simulated active_hours and wait_hours. These are integration instructions; no log merger or cross-provider mining result is included.
