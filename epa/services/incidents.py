import os
from datetime import datetime
from typing import Annotated
from urllib.parse import quote
import httpx
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .common import Store, Command, principal, authorise
from .domain import transition
from .read_api import register_read_api
from .validation import validate_values


class Report(BaseModel):
    model_config=ConfigDict(extra='forbid', str_strip_whitespace=True)
    category: str = Field(min_length=2,max_length=50)
    location: str = Field(min_length=3,max_length=300)
    description: str = Field(min_length=10,max_length=2000)
    observed_at: datetime
    licence_id: str|None = None
    emergency: bool = False

    @field_validator('observed_at')
    @classmethod
    def timezone_required(cls,value):
        if value.tzinfo is None:
            raise ValueError('Include timezone, for example 2026-10-01T10:00:00+10:00')
        return value


def create_app(db_path=None,context_loader=None,identity_dependency=None):
    store=Store(db_path or os.getenv('NZ_INCIDENT_DB','data/incidents.sqlite'))
    app=FastAPI(title='NetZero NSW EPA Incident Prototype',version='2.0.0', root_path=os.getenv('NZ_ROOT_PATH',''),
                description='Educational prototype. Never use this application to report an actual emergency or fulfil notification duties.')
    app.state.store=store
    if identity_dependency is not None:
        app.dependency_overrides[principal] = identity_dependency
    register_read_api(app, store)

    def lookup(licence_id):
        if context_loader:
            return context_loader(licence_id)
        try:
            response=httpx.get(os.getenv('NZ_LICENCE_URL','http://127.0.0.1:8001')+
                               '/internal/licences/'+quote(licence_id, safe='')+'/context',
                               headers={'Authorization':'Bearer '+os.getenv('NZ_INTERNAL_TOKEN','demo-internal-token')},timeout=2.0,trust_env=False)
            if response.status_code==404:
                return {'summary':'No matching prototype licence','match':False}
            response.raise_for_status()
            return {'summary':'Licence context retrieved over HTTP','match':True,'licence':response.json()}
        except (httpx.HTTPError,ValueError) as e:
            raise HTTPException(503,'Licence lookup unavailable; retry this task later. Incident remains saved.') from e

    @app.get('/health')
    def health():
        return {'service':'incidents','status':'ok','mode':'prototype'}

    @app.post('/incidents',status_code=201)
    def submit(payload:Report,user=Depends(principal),idempotency_key:Annotated[str|None,Header()]=None):
        result=store.create('P3',payload.model_dump(mode='json'),user,idempotency_key)
        result=dict(result)
        result['guidance']='For immediate danger call 000. Real EPA reports use official channels including 131 555. This prototype sends no reports.'
        return result

    @app.get('/cases/{case_id}')
    def get_case(case_id:str,user=Depends(principal)):
        case=store.get(case_id);authorise(user,case);return case

    @app.post('/cases/{case_id}/commands')
    def command(case_id:str,command:Command,user=Depends(principal)):
        authorise(user,officer=True)
        case=store.get(case_id)
        values=validate_values(case['process'], command.action, command.values)
        if command.action=='review_licence':
            case=store.get(case_id)
            licence_id=case['data'].get('licence_id')
            values=lookup(licence_id) if licence_id else {'summary':'No licence reference supplied','match':False}
        return store.apply(case_id,command.expected_version,user,
                           lambda case,db: transition(case,command.action,values))

    @app.get('/events')
    def events(user=Depends(principal)):
        authorise(user,officer=True);return store.events()
    return app
