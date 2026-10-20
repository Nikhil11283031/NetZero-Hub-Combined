"""Validate command payloads at the HTTP boundary, before domain transitions."""
from typing import Annotated
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints, ValidationError

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Reference = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
References = Annotated[list[Reference], Field(max_length=20)]

class Empty(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Supply(Empty):
    documents: References | None = None
    fee_reference: Reference | None = None
    consent_reference: Reference | None = None

class Assessment(Empty):
    passed: StrictBool
    rationale: Text

class Decision(Empty):
    approved: StrictBool
    rationale: Text
    conditions: Annotated[list[Text], Field(min_length=1, max_length=20)] | None = None

class Reason(Empty):
    rationale: Text

class Triage(Empty):
    emergency: StrictBool
    epa_jurisdiction: StrictBool

class Evidence(Empty):
    summary: Text

class Conclusion(Reason):
    substantiated: StrictBool

SCHEMAS = {
    'P1': {'check': Empty, 'supply': Supply, 'assess_environment': Assessment,
           'assess_suitability': Assessment, 'decide': Decision, 'expire': Reason},
    'P2': {'verify': Empty, 'assess': Assessment, 'decide': Decision},
    'P3': {'triage': Triage, 'collect_evidence': Evidence, 'review_licence': Empty, 'conclude': Conclusion},
}

def validate_values(process, action, values):
    schema = SCHEMAS.get(process, {}).get(action)
    if schema is None:
        raise HTTPException(409, 'Unknown action for this process')
    try:
        return schema.model_validate(values).model_dump(exclude_none=True)
    except ValidationError as exc:
        raise HTTPException(422, [{'loc': ['values', *e['loc']], 'msg': e['msg'], 'type': e['type']}
                                  for e in exc.errors()]) from exc
