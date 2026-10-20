# Combined portal integration

## Frontend

`frontend/src/pages/Dashboard.jsx` imports the EPA leaf SVG from `components/ui.jsx`. The Environment Protection card links to `/epa/cases` and `/epa`. Its count comes from accessible, unfinished cases in both EPA services, rather than the group's previous placeholder count. An unavailable count displays a dash.

`App.jsx` protects `/epa/*` with the existing login guard and retains the signed-in Dashboard navigation link. Old `/environment` and `/environment/new` links redirect to the corresponding EPA pages. `/bookings` is now an explicit route.

`features/epa/Portal.jsx` embeds the EPA pages inside the existing React Router and supplies the current group identity. The standalone EPA login and second app shell are not mounted. The project keeps the group's React 18 / Router 6 versions.

Bootstrap is generated under the `.epa-app` selector by `scripts/build-epa-css.mjs` during development and builds. This contains its reset and components within the EPA area. EPA custom styling is also scoped.

## Public and internal routes

| Browser prefix | Docker destination | Forwarded path example |
| --- | --- | --- |
| `/api/v1/epa/licensing/` | `epa-licensing:8001` | `/cases` |
| `/api/v1/epa/incidents/` | `epa-incidents:8002` | `/cases` |
| Other `/api/`, `/admin/`, `/static/` | `backend:8000` | Original path |
| Application pages | Frontend nginx | React `index.html` fallback |

The EPA nginx locations take precedence over the generic Django API location. Each EPA service receives its public prefix as `NZ_ROOT_PATH` so generated OpenAPI URLs work through the proxy. Vite has equivalent proxy rules for development.

EPA services do not publish host ports in Compose. The incident service retrieves licence context from `http://epa-licensing:8001/internal/licences/{id}/context`, using `NZ_INTERNAL_TOKEN`. This key stays in backend environment variables and is not supplied to React.

## Authentication and ownership

1. Existing Django login returns an opaque token and serialized user.
2. React sends `Authorization: Token <token>` to either EPA service.
3. `epa/services/portal.py` verifies it against the fixed `NZ_AUTH_URL` (`backend:8000/api/v1/auth/me/`). It does not follow redirects or cache tokens.
4. Django computes `epa_role` from superuser status or membership in `EPA Officers`.
5. EPA uses `django:<user ID>` as its stable owner identifier. Existing domain checks restrict clients to their records and officers to permitted workflow commands.

Logging out revokes the Django token; subsequent EPA requests are rejected. If identity verification is unavailable, EPA returns 503 instead of accepting unverified users. Registration cannot assign an officer role. The combined factories reject the former public demo tokens. The private internal key only grants the limited licence-context role.

`backend/recycling/epa_roles.py`, `UserSerializer` and `seed_data` implement this role integration without changing the group user model or existing passwords. `SQLITE_PATH` is an optional local-development override; Docker still uses MySQL.

## Storage and deployment

Compose retains the original name `recycling-scheduling` and MySQL volume. It adds persistent, separate SQLite volumes for the two EPA APIs. Source code is packaged together, while services remain separately deployable processes. Existing EPA demonstration owners are not migrated to Django owners automatically.

The setup helper adds missing variables and fills empty or `CHANGE-ME` secrets. Existing configured values are preserved. The combined project must use the original `.env` when retaining an existing MySQL volume.

The EPA services now depend on the group authentication API. During a Django outage, new EPA authenticated requests fail with a retryable availability error; health endpoints only report that the individual API process is responding.

## Group development

EPA UI changes belong under `frontend/src/features/epa/`; EPA business logic belongs under `epa/services/`. Recycling and solar retain their existing folders. Shared route, authentication, navigation and Compose changes should be reviewed together before merging.

The Vite configuration expects API processes directly on ports 8000, 8001 and 8002 for development outside Docker. Those EPA host ports are not exposed by Compose. For the Docker workflow, rebuild from the project root as described in README.md.
