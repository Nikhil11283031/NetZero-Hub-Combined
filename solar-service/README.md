# Solar Panel Installation microservice (ORG-001)

Part of NetZero Hub. Customers request a solar installation, book a free site assessment, get a quote, pay
(10% deposit, in full, or the balance) and follow the request until it is installed. Installer staff move
requests through their stages.

This is a **separate microservice**: its own Django project, its own MySQL database (`solar-db`) and its own
container. It shares no tables with any other service.

## Architecture

```
                 browser
                    │
        frontend container (nginx = API gateway)
           │                               │
 /api/v1/solar/...                    other /api/...
           │                               │
   ┌───────▼────────┐  GET /auth/me/  ┌────▼────────────────┐
   │ solar-service  │ ──────────────► │ backend (Django) │
   │ Django + DRF   │  (check token)  │ + group accounts    │
   └───────┬────────┘                 └────┬────────────────┘
           │                               │
     ┌─────▼─────┐                    ┌────▼────┐
     │ solar-db  │                    │   db    │
     │ (MySQL)   │                    │ (MySQL) │
     └───────────┘                    └─────────┘
```

- **Database per service.** Solar's tables (`solar_solarrequest`, `solar_solarrequestevent`,
  `solar_solarpayment`) live only in `solar-db`.
- **One login for the whole hub.** User accounts belong to the group's Django backend. Solar has no user table:
  for each request it sends the caller's `Authorization: Token …` header to `GET /api/v1/auth/me/`
  (`NZ_AUTH_URL`) and gets back the user's id, username, name and `is_staff`, the same way the EPA services
  verify identity. Tokens are not cached by default, so signing out takes effect straight away. See `solar/auth.py`.
- **References, not foreign keys.** A solar request stores the customer's `user_id` and `username` instead of a
  database link to another service's table.
- **API composition.** The shared dashboard asks each service for its own count (solar:
  `GET /api/v1/solar/summary/`) instead of reading other databases.
- **Fails safely.** If the accounts service is down, solar answers `503` instead of letting anyone in.

## API (all under `/api/v1/solar/`)

| Method | Path | Who | What |
| --- | --- | --- | --- |
| GET | `health/` | anyone | Liveness check |
| GET | `options/`, `postcode/?postcode=`, `recommend/?quarterly_usage_kwh=` | anyone | Reference data |
| GET | `availability/` | signed in | Free site-assessment slots |
| GET / POST | `requests/` | signed in | List (`?scope=upcoming`) or create a request |
| GET | `requests/{reference}/` | owner | One request with quote, payments and timeline |
| POST | `requests/{reference}/pay/` | owner | Pay deposit / full / balance (demo card) |
| POST | `requests/{reference}/cancel/` | owner | Cancel (refunds anything paid) |
| GET | `summary/` | signed in | Active request count, for the dashboard |
| GET | `admin/summary/`, `admin/requests/` | staff | Staff overview and search |
| POST | `admin/requests/{reference}/status/` | staff | Move to Site assessed / Installed / Cancelled |

Interactive docs: `/api/v1/solar/docs/`.

## Running it

**With Docker** (from the repo root): `docker compose up --build`. This starts `solar-db` and `solar-service`
alongside the other services. `python scripts/setup_env.py` fills in the `SOLAR_*` passwords in `.env`.

**Without Docker** (for development), in three terminals:

```bash
# 1. group accounts + recycling (port 8000)
cd backend && python3 manage.py migrate && python3 manage.py runserver

# 2. solar service (port 8003), using its own SQLite file solar.sqlite3
#    (needs the same Python packages as backend/, so nothing new to install)
cd solar-service && python3 manage.py migrate && python3 manage.py runserver 8003

# 3. website (port 5173); the dev server sends /api/v1/solar to port 8003
cd frontend && npm install && npm run dev
```

## Tests

```bash
cd solar-service && python3 manage.py test
```

26 tests: booking rules and slot capacity, payments and refunds, staff workflow, privacy between customers, and
the remote sign-in check (valid token checked on every request, optional cache, invalid token, accounts service down).
