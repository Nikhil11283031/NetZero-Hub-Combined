# NetZero Hub — combined group project

One React website and one Docker Compose setup for the group's recycling and solar services, plus the NSW EPA licensing and incident services. Sign in once using the group account.

The Environment Protection dashboard card uses the original EPA green leaf. **View Requests** opens `/epa/cases`; **New Request** opens `/epa`. With Docker, both pages use port **3000**. The separate EPA website on port 5173 is no longer needed.

## Start on Windows with your existing group database

Keep the original group folder as a backup. Download this archive into Downloads, then run these commands in PowerShell. Docker Desktop must be running.

```powershell
cd "C:\Users\nashl\Downloads\NetZero-Hub-main\NetZero-Hub-main"
docker compose stop

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\NetZero-Hub-Combined.zip" -DestinationPath "$env:USERPROFILE\Downloads"
cd "$env:USERPROFILE\Downloads\NetZero-Hub-Combined"

Copy-Item -LiteralPath "C:\Users\nashl\Downloads\NetZero-Hub-main\NetZero-Hub-main\.env" -Destination ".env"
python scripts/setup_env.py
docker compose up --build -d
docker compose ps
```

If you extracted the ZIP manually, open the folder that directly contains `docker-compose.yml`; skip `Expand-Archive` and change into that folder instead.

**Copy the existing `.env` before running the setup helper.** The helper preserves its configured passwords and generates the missing EPA internal key. MySQL keeps its existing credentials when its volume is reused; generating different database passwords would prevent the backend connecting.

The Compose project name stays `recycling-scheduling`, matching the supplied group project, so its existing `mysql-data` volume is reused. This assumes you previously started the project normally, without a different `-p` project name. Check `docker compose ls` if unsure, and use the same project name for both versions.

Open **http://localhost:3000/login**, sign in, and choose **Dashboard**. The first build downloads dependencies and can take several minutes.

| Page | Address |
| --- | --- |
| Shared dashboard | http://localhost:3000/dashboard |
| EPA new request / overview | http://localhost:3000/epa |
| EPA cases | http://localhost:3000/epa/cases |
| EPA licences | http://localhost:3000/epa/licences |
| Recycling collections | http://localhost:3000/bookings |
| Solar requests | http://localhost:3000/solar |
| Django administration | http://localhost:3000/admin/ |

## First installation for another group member

From the folder containing `docker-compose.yml`:

```powershell
python scripts/setup_env.py
docker compose up --build -d
```

The helper creates a local `.env` with random service secrets. It supplies these local demonstration passwords when the corresponding values are blank:

| Account | Default password | Access |
| --- | --- | --- |
| `resident` | `Resident927!Local` | Own recycling, solar and EPA records |
| `provider_admin` | `Provider927!Local` | Group administration, provider console and EPA officer workspace |

For an existing installation, continue using its existing passwords. Seeding does not reset existing users' passwords. Normal users can also register through the website. These defaults are for the local university demonstration.

## Everyday commands

Run commands from this combined project folder:

```powershell
# After a PC restart: open Docker Desktop, then start the stack.
docker compose up -d

# After changing source code, rebuild the affected images.
docker compose up --build -d

# See status or recent errors.
docker compose ps
docker compose logs --tail=100 backend solar-service epa-licensing epa-incidents frontend

# Stop without deleting saved data.
docker compose stop
```

Do not run `docker compose down -v` unless you deliberately want to delete the project's saved databases.

If only frontend files changed, use `docker compose up -d --build --no-deps frontend`, then refresh the browser. Local source files are copied into images at build time.

## What runs together

| Folder / service | Responsibility | Technology / data |
| --- | --- | --- |
| `frontend/` → `frontend` | Shared header, login, dashboard and all provider pages; nginx routes API requests | React 18, React Router 6, Vite 5 |
| `backend/` → `backend` | Group accounts and recycling API | Django REST Framework, MySQL |
| `backend/` → `scheduler` | Existing recycling reminders and timetable maintenance | Django commands |
| `solar-service/` → `solar-service` | Solar installation requests, quotes, payments and staff workflow | Django REST Framework, its own MySQL database (`solar-db`) |
| `epa/` → `epa-licensing` | Licence applications and variations, events and exports | FastAPI, persistent SQLite volume |
| `epa/` → `epa-incidents` | Pollution reports and investigations, licence context lookup, events and exports | FastAPI, separate persistent SQLite volume |
| `db` | Group database (accounts and recycling) | MySQL 8.4, existing persistent volume |
| `solar-db` | Solar database | MySQL 8.4, separate `solar-mysql-data` volume |

All source is in this folder. The services retain their own runtimes and data stores. The EPA databases do not move into MySQL. No separate host installation of Django, FastAPI, npm packages or MySQL is needed to run Docker; the setup helper uses your installed Python.

EPA and solar requests use the same opaque login token as the group API. Each EPA service and the solar service ask Django to verify it. EPA officer access requires a superuser or membership in the **EPA Officers** Django group; ordinary provider staff are not automatically EPA officers.

To add an EPA officer, sign into `/admin/` as `provider_admin`, open the user, add **EPA Officers** under Groups and save. The user should sign out and back in so the frontend refreshes their role. They do not need `is_staff` merely to use the EPA workspace.

## Data and previous EPA records

The shared group database is preserved when you reuse its `.env` and Compose project name. The new EPA services start with empty databases and persist new records in `epa-licence-data` and `epa-incident-data` volumes.

Old standalone EPA records are not automatically imported. They belong to standalone demo identities, while this version assigns ownership to Django user IDs. Keep the standalone folder if you need those records; copying its SQLite files directly would not correctly map ownership. Existing report diagrams, models and simulated analytics are retained under `epa/`.

## Documentation and checks

- `docs/INTEGRATION.md`: route mappings, identity, data and files changed.
- `docs/VERIFICATION.md`: checks completed and remaining Docker verification.
- `docs/RECYCLING_REFERENCE.md`: original group recycling documentation, retained as a historical reference.
- `epa/README.md`: EPA processes and retained standalone materials.

Current API documentation is served at `/api/docs/` for Django, `/api/v1/solar/docs/` for solar, `/api/v1/epa/licensing/docs` for licensing, and `/api/v1/epa/incidents/docs` for incidents.

Do not commit `.env`, local databases, dependencies or generated browser test output. `.gitignore` excludes them. Share source through the group's repository; each member creates their own `.env`.
