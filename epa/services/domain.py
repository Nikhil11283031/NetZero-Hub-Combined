"""Business transitions shared by HTTP services and the seeded simulator.

These are proposed NetZero Hub workflows, not NSW EPA's internal software.
No function submits an application, notifies an authority, or makes a legal decision.
"""
from copy import deepcopy

TASKS = {
    'A1': ('Receive application', 'Intake'),
    'A2': ('Check completeness', 'Licensing officer'),
    'A3': ('Request information', 'Licensing officer'),
    'A4': ('Receive information', 'Applicant'),
    'A5': ('Close incomplete case', 'Licensing officer'),
    'A6': ('Assess environmental impacts', 'Environmental assessor'),
    'A7': ('Check suitability and consent', 'Licensing officer'),
    'A8': ('Decide application', 'Decision officer'),
    'A9': ('Issue prototype licence', 'Licence service'),
    'A10': ('Record application refusal', 'Decision officer'),
    'A11': ('Publish application outcome', 'Licence service'),
    'V1': ('Receive variation request', 'Intake'),
    'V2': ('Verify licence eligibility', 'Licensing officer'),
    'V3': ('Record invalid variation', 'Licensing officer'),
    'V4': ('Assess proposed change', 'Environmental assessor'),
    'V5': ('Decide variation', 'Decision officer'),
    'V6': ('Update licence conditions', 'Licence service'),
    'V7': ('Record variation refusal', 'Decision officer'),
    'V8': ('Publish variation outcome', 'Licence service'),
    'I1': ('Register pollution report', 'Intake'),
    'I2': ('Triage risk and jurisdiction', 'Intake officer'),
    'I3': ('Provide emergency guidance', 'Intake officer'),
    'I4': ('Record referral guidance', 'Intake officer'),
    'I5': ('Assign investigator', 'Investigation manager'),
    'I6': ('Collect evidence', 'Investigator'),
    'I7': ('Review licence context', 'Investigator'),
    'I8': ('Assess evidence', 'Investigator'),
    'I9': ('Record regulatory action', 'Decision officer'),
    'I10': ('Record no further action', 'Decision officer'),
    'I11': ('Close investigation', 'Investigation manager'),
    'I12': ('Publish incident outcome', 'Incident service'),
}


class DomainError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise DomainError(message)


def transition(case, action, values):
    """Return a new case and ordered completed task IDs; never mutate input."""
    case = deepcopy(case)
    d, state, process = case['data'], case['state'], case['process']
    events = []
    if process == 'P1':
        if action == 'check':
            require(state == 'SUBMITTED', 'Completeness check requires SUBMITTED')
            complete = bool(d.get('documents') and d.get('fee_reference') and d.get('consent_reference'))
            events = ['A2']
            case['state'] = 'ASSESSMENT' if complete else 'AWAITING_INFORMATION'
            if not complete:
                events.append('A3')
        elif action == 'supply':
            require(state == 'AWAITING_INFORMATION', 'No information request is open')
            d.update({k: values[k] for k in ('documents', 'fee_reference', 'consent_reference') if k in values})
            case['state'] = 'SUBMITTED'
            events = ['A4']
        elif action in ('assess_environment', 'assess_suitability'):
            require(state == 'ASSESSMENT', 'Assessment requires a complete application')
            key = 'environment' if action == 'assess_environment' else 'suitability'
            require(key not in d, 'This assessment has already been recorded')
            require(isinstance(values.get('passed'), bool), 'passed must be a boolean')
            require(bool(values.get('rationale')), 'An assessment rationale is required')
            d[key] = {'passed': values['passed'], 'rationale': values['rationale']}
            events = ['A6' if key == 'environment' else 'A7']
        elif action == 'decide':
            require(state == 'ASSESSMENT' and 'environment' in d and 'suitability' in d,
                    'Both assessments must finish before a decision')
            require(isinstance(values.get('approved'), bool) and bool(values.get('rationale')),
                    'A decision and rationale are required')
            approved = values['approved']
            require(not approved or (d['environment']['passed'] and d['suitability']['passed']),
                    'Approval requires both assessments to pass')
            case['state'] = 'APPROVED' if approved else 'REFUSED'
            d['decision_rationale'] = values['rationale']
            if approved:
                d['licence_id'] = 'NZ-' + case['id']
                d['conditions'] = values.get('conditions', ['Operate only within recorded conditions'])
            events = ['A8', 'A9' if approved else 'A10', 'A11']
        elif action == 'expire':
            require(state == 'AWAITING_INFORMATION', 'Only an awaiting-information case can expire')
            require(bool(values.get('rationale')), 'Closure reason is required')
            case['state'] = 'INCOMPLETE_CLOSED'
            d['decision_rationale'] = values['rationale']
            events = ['A5', 'A11']
        else:
            raise DomainError('Unknown application action')
    elif process == 'P2':
        if action == 'verify':
            require(state == 'SUBMITTED', 'Verification requires SUBMITTED')
            require(isinstance(values.get('eligible'), bool), 'eligible must be a boolean')
            d['eligible'] = values['eligible']
            case['state'] = 'ASSESSMENT' if values['eligible'] else 'INVALID'
            events = ['V2'] if values['eligible'] else ['V2', 'V3', 'V8']
        elif action == 'assess':
            require(state == 'ASSESSMENT' and 'assessment' not in d, 'Variation not ready for assessment')
            require(isinstance(values.get('passed'), bool) and bool(values.get('rationale')),
                    'Assessment result and rationale are required')
            d['assessment'] = values
            events = ['V4']
        elif action == 'decide':
            require(state == 'ASSESSMENT' and 'assessment' in d, 'Variation assessment is required')
            require(isinstance(values.get('approved'), bool) and bool(values.get('rationale')),
                    'Decision and rationale are required')
            require(not values['approved'] or d['assessment']['passed'], 'Failed assessment cannot be approved')
            case['state'] = 'APPROVED' if values['approved'] else 'REFUSED'
            d['decision_rationale'] = values['rationale']
            events = ['V5', 'V6' if values['approved'] else 'V7', 'V8']
        else:
            raise DomainError('Unknown variation action')
    elif process == 'P3':
        if action == 'triage':
            require(state == 'SUBMITTED', 'Triage requires SUBMITTED')
            require(isinstance(values.get('emergency'), bool) and isinstance(values.get('epa_jurisdiction'), bool),
                    'Triage must record both risk and jurisdiction')
            d.update(values)
            events = ['I2']
            if values['emergency']:
                case['state'] = 'EMERGENCY_GUIDANCE'
                d['outcome'] = 'Call 000 for an immediate threat. This prototype has not contacted emergency services.'
                events += ['I3', 'I12']
            elif not values['epa_jurisdiction']:
                case['state'] = 'REFERRED'
                d['outcome'] = 'Contact the responsible authority. No information has been transmitted to it.'
                events += ['I4', 'I12']
            else:
                case['state'] = 'INVESTIGATION'
                events += ['I5']
        elif action in ('collect_evidence', 'review_licence'):
            require(state == 'INVESTIGATION', 'Case is not under investigation')
            key = 'evidence' if action == 'collect_evidence' else 'licence_context'
            require(key not in d, 'This investigation task is already complete')
            require(bool(values.get('summary')), 'A review summary is required')
            d[key] = values
            events = ['I6' if key == 'evidence' else 'I7']
        elif action == 'conclude':
            require(state == 'INVESTIGATION' and 'evidence' in d and 'licence_context' in d,
                    'Evidence and licence review must both be complete')
            require(isinstance(values.get('substantiated'), bool) and bool(values.get('rationale')),
                    'Conclusion and rationale are required')
            d['substantiated'] = values['substantiated']
            d['outcome'] = values['rationale']
            case['state'] = 'ACTION_RECORDED' if values['substantiated'] else 'NO_FURTHER_ACTION'
            events = ['I8', 'I9' if values['substantiated'] else 'I10', 'I11', 'I12']
        else:
            raise DomainError('Unknown incident action')
    else:
        raise DomainError('Unknown process')
    return case, events
