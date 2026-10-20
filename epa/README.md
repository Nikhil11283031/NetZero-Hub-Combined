# NSW EPA module in NetZero Hub

Use the **root README.md** to start the combined project. The UI is in `../frontend/src/features/epa`; the two API services are here.

| Service | Processes |
| --- | --- |
| EPA001 — Environment protection licensing | P1 application assessment and decision; P2 licence variation |
| EPA002 — Pollution incident handling | P3 triage, investigation and outcome |

Compose starts `services.portal:create_licensing_app` and `services.portal:create_incident_app`. These entry points use the shared Django login. The original factories remain available for isolated domain tests; they use the old demonstration identity mechanism and are not the Compose entry points.

The officer workspace supports case commands and CSV/XES event export. Incident investigation can retrieve the latest licence context over HTTP from the licensing service.

`models/`, `diagrams/`, `analytics/` and `results/` retain the earlier modelling and simulation materials. Files under `docs/` describe the earlier standalone package and are labelled accordingly. `demo.py` also targets the original standalone demo-token setup; do not use it as the combined-stack smoke test. The current shared-login checks are in `../frontend/tests/browser/combined.spec.js`.

For the current integration design and validation, read `../docs/INTEGRATION.md` and `../docs/VERIFICATION.md`.
