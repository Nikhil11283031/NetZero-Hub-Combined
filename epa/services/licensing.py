import json
import os
from datetime import datetime, timezone, timedelta
from typing import Annotated
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from .common import Store, Command, principal, authorise
from .domain import transition, require
from .read_api import register_read_api
from .validation import validate_values, Reference


class Application(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    applicant: str = Field(min_length=2,max_length=150)
    premises: str = Field(min_length=3,max_length=300)
    activity: str = Field(min_length=3,max_length=500)
    consent_reference: str | None = Field(default=None,max_length=200)
    fee_reference: str | None = Field(default=None,max_length=200)
    documents: list[Reference] = Field(default_factory=list,max_length=20)


class Variation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    licence_id: Reference
    proposed_conditions: list[Reference] = Field(min_length=1,max_length=20)
    rationale: str = Field(min_length=3,max_length=1000)


def create_app(db_path=None, clock=None, identity_dependency=None):
    store = Store(db_path or os.getenv('NZ_LICENCE_DB','data/licensing.sqlite'))
    now = clock or (lambda: datetime.now(timezone.utc))
    app = FastAPI(title='NetZero NSW EPA Licence Prototype',version='2.0.0', root_path=os.getenv('NZ_ROOT_PATH',''),
                  description='Educational prototype. No real EPA applications, fees or decisions are processed.')
    app.state.store = store
    if identity_dependency is not None:
        app.dependency_overrides[principal] = identity_dependency
    register_read_api(app, store, licences=True)

    @app.get('/health')
    def health():
        return {'service':'licensing','status':'ok','mode':'prototype'}

    @app.post('/applications', status_code=201)
    def submit(payload:Application,user=Depends(principal),idempotency_key:Annotated[str|None,Header()]=None):
        return store.create('P1',payload.model_dump(),user,idempotency_key)

    @app.post('/variations',status_code=201)
    def vary(payload:Variation,user=Depends(principal),idempotency_key:Annotated[str|None,Header()]=None):
        authorise(user)
        licence=store.get_licence(payload.licence_id)
        if licence['owner'] != user['subject'] and user['role'] != 'officer':
            raise HTTPException(403,'Only the licence owner or an officer can request a variation')
        data=payload.model_dump()
        data['licence_version']=licence['version']
        # Fingerprint excludes a mutable licence version, so replaying the same POST
        # still returns the same case after that licence has changed.
        with store.connect() as db:
            old=db.execute('SELECT case_id FROM idempotency WHERE scope=? AND key=?',
                           (user['subject']+':P2',idempotency_key)).fetchone()
            if old:
                previous=store.get(old['case_id'])
                data['licence_version']=previous['data']['licence_version']
        return store.create('P2',data,user,idempotency_key)

    @app.get('/cases/{case_id}')
    def get_case(case_id:str,user=Depends(principal)):
        case=store.get(case_id);authorise(user,case);return case

    @app.post('/cases/{case_id}/commands')
    def command(case_id:str,command:Command,user=Depends(principal)):
        authorise(user,officer=command.action!='supply')
        def apply(case,db):
            values=validate_values(case['process'], command.action, command.values)
            if case['process']=='P2':
                lic=store.get_licence(case['data']['licence_id'],db)
                if command.action=='verify':
                    values={'eligible':lic['active'] and lic['version']==case['data']['licence_version']}
                if command.action=='decide' and values.get('approved'):
                    require(lic['active'] and lic['version']==case['data']['licence_version'],
                            'Licence changed since this variation was submitted; create a fresh variation')
            if command.action=='expire':
                due=case['data'].get('information_due_at')
                require(bool(due) and now()>=datetime.fromisoformat(due),'Information timer has not elapsed')
            if command.action=='supply':
                due=case['data'].get('information_due_at')
                require(bool(due) and now()<datetime.fromisoformat(due),
                        'Information deadline has elapsed; an officer must close the case')
            new,ids=transition(case,command.action,values)
            if new['state']=='AWAITING_INFORMATION' and 'A3' in ids:
                new['data']['information_due_at']=(now()+timedelta(days=30)).isoformat()
            if 'A4' in ids or 'A5' in ids:
                new['data'].pop('information_due_at',None)
            if 'A9' in ids:
                lic={'id':new['data']['licence_id'],'owner':new['owner'],'active':True,'version':1,
                     'conditions':new['data']['conditions'],'source_case':new['id']}
                db.execute('INSERT INTO licences VALUES (?,?)',(lic['id'],json.dumps(lic)))
            if 'V6' in ids:
                lic['conditions']=new['data']['proposed_conditions'];lic['version']+=1
                db.execute('UPDATE licences SET body=? WHERE id=?',(json.dumps(lic),lic['id']))
            return new,ids
        return store.apply(case_id,command.expected_version,user,apply)

    @app.get('/licences/{licence_id}')
    def get_licence(licence_id:str,user=Depends(principal)):
        licence=store.get_licence(licence_id)
        authorise(user,{'owner':licence['owner']});return licence

    @app.get('/internal/licences/{licence_id}/context')
    def context(licence_id:str,user=Depends(principal)):
        if user['role'] not in ('internal','officer'):
            raise HTTPException(403,'Service or officer token required')
        licence=store.get_licence(licence_id)
        return {k:licence[k] for k in ('id','active','version','conditions')}

    @app.get('/events')
    def events(user=Depends(principal)):
        authorise(user,officer=True);return store.events()
    return app
