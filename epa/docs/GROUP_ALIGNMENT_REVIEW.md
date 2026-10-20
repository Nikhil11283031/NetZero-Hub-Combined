> Retained from the earlier standalone EPA package. Its setup, authentication and integration status describe that version. For the combined project, use ../../README.md and ../../docs/INTEGRATION.md.

# EPA report alignment review

The EPA contribution still fits the group project: one provider, two business services and three processes. This review used the supplied group work to check consistency. That work is not cited as an academic source in the EPA report.

## Changes made to the EPA report

| Area | Change and reason |
|---|---|
| A: service catalogue | Standardised the report and model labels to EPA-001 and EPA-002. The existing UI labels EPA001 and EPA002 are explained as aliases. |
| B: process identifiers | Preserved the local P1/P2/P3 and task IDs so the models, implementation and logs still match. Explained provider-qualified labels such as EPA.P1.A1 for the combined report. |
| C: contracts and composition | Clarified that the Hub provides the shared user experience and consumes the EPA APIs. Added the main contract effects and explained how polling can coexist with another provider's callback contract. |
| D: enterprise architecture | Added the existing React feature module and web delivery/API proxy to the diagram and native ArchiMate model. |
| E: implementation | Replaced the outdated API-only description with the implemented React frontend, two FastAPI services, separate databases, actual routes and integration boundary. Updated the deployment diagram and reproduction steps. |
| E: verification | Used the existing evidence for 19 API tests, seven frontend helper tests, six browser workflows run individually and the live HTTP composition. No application tests were rerun for this documentation change. Docker/Nginx and the shared group login remain unverified. |
| F: event logs | Distinguished live API activity from the seeded experiment. Added instructions for provider-qualified case/task IDs and a consistent XES classifier before any group analysis. |
| References | Retained the official and original sources with website links. No group draft, lecture slide or previous-semester report was added to the bibliography. |

The application source and recorded analytics results were retained. Part G remains a worksheet for actual work and peer agreement; other members' contribution claims were not copied.

## Issues for the group to resolve

| Priority | Finding in the supplied draft | Required action |
|---|---|---|
| High | Part A identifies Cleanaway as the waste provider, while the waste BPMN uses Wollongong City Council and Remondis Harbour Cities. The prose also varies the contractor spelling. | Choose and justify one provider arrangement. Use the same identities and responsibilities throughout A–D, and verify any real-world provider relationship from an official source. |
| High | Part A contains four named providers with two service specifications each. Public transport appears later but lacks its complete Part A provider/service entries in this attachment. | Add the transport provider and two full service specifications, or include another qualifying provider, to meet the five-provider minimum. |
| High | The transport BPMN concerns card application/eligibility; the architecture describes tap-on/tap-off and journey planning. | Map these processes explicitly to the selected services. Add missing process coverage or revise the architecture so the relationship is clear. |
| High | Both exits from the waste date-availability gateway are labelled Yes, although one leads to rejection. | Label the available and unavailable branches consistently and check the corresponding guards/effects. |
| High | The waste resubmission step uses set union to add submitted(o) after rejection added its negation. | Use the stated accumulation rule to remove the conflicting older literal. If the date changes, replace the old functional date value as well. Recheck the resulting scenario for consistency. |
| Medium | The waste reasoning infers no recycling selection from absence under a one-way rule. | Add an explicit complete-selection/closed-world assumption or a suitable equivalence. Absence alone does not establish negation in ordinary first-order logic. |
| Medium | Some cumulative contract scenarios omit earlier compatible effects; the missed-collection scenario leaves optional payment unresolved. | Retain compatible history and distinguish paid/unpaid variants where their effects differ. Check that every claimed postcondition follows from the accumulated effects. |
| Medium | Several penalties, discounts and refunds are stated as provider promises without support visible in this attachment. | Identify them as proposed project terms or support them with the provider's actual published terms. Do not present invented guarantees as official policy. |
| Medium | Some source notes refer to a group rough report, and this attachment has no final references section. | Replace those notes with the original relevant sources and include a matching bibliography in the combined report. |
| Integration | This attachment does not establish a common framework, identity system, runnable implementation or complete E–G evidence. That does not establish whether members have completed them elsewhere. | Collect the actual repository/code, authentication decision, API contracts, execution logs and contribution evidence before claiming group integration is complete. |

## Decisions needed before merging the implementation

1. Agree the shared React router and navigation. The EPA feature can mount at `/epa/*`.
2. Agree verified user identity and trusted roles. The EPA demo account selector is not a shared authentication system.
3. Confirm the two API prefixes and proxy mapping. Other providers should call EPA APIs rather than access its databases.
4. Agree log naming and classifiers. Keep live timings separate from virtual simulation durations, and do not merge unrelated cases merely because they share a user.
5. Run a combined demonstration with another provider's implemented service. If the team chooses Compose, execute and check the supplied container configuration on the group machine.

The supplied draft gives no reason by itself to replace the EPA FastAPI backend with Django. Frontend integration, identity, contracts and data ownership are the decisions that need to align.
