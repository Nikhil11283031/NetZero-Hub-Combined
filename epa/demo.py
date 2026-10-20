"""Exercise all three processes over real local HTTP; requires python run.py."""
import json
import os
import uuid
from datetime import datetime,timezone
from pathlib import Path
import httpx

C={'Authorization':'Bearer demo-client-token'}
O={'Authorization':'Bearer demo-officer-token'}

def create(base,path,payload):
    r=httpx.post(base+path,json=payload,headers={**C,'Idempotency-Key':uuid.uuid4().hex},trust_env=False);r.raise_for_status();return r.json()

def act(base,case,action,values=None,headers=O):
    r=httpx.post(base+'/cases/'+case['id']+'/commands',headers=headers,
                 json={'expected_version':case['version'],'action':action,'values':values or {}},trust_env=False)
    r.raise_for_status();return r.json()

def main():
    licence=os.getenv('NZ_DEMO_LICENCE_URL','http://127.0.0.1:8001')
    incident=os.getenv('NZ_DEMO_INCIDENT_URL','http://127.0.0.1:8002')
    a=create(licence,'/applications',{'applicant':'Demo Recycling Pty Ltd','premises':'Demo site Wollongong',
       'activity':'Demonstration resource recovery','fee_reference':'SIMULATED-FEE','consent_reference':'SIMULATED-CONSENT'})
    a=act(licence,a,'check')
    a=act(licence,a,'supply',{'documents':['demo-site-plan.pdf']},C)
    a=act(licence,a,'check')
    for action in ['assess_environment','assess_suitability']:
        a=act(licence,a,action,{'passed':True,'rationale':'Educational demonstration only'})
    a=act(licence,a,'decide',{'approved':True,'rationale':'Both prototype assessments passed','conditions':['Demo condition 1']})
    licence_id=a['data']['licence_id']
    v=create(licence,'/variations',{'licence_id':licence_id,'proposed_conditions':['Demo revised condition'],
                                 'rationale':'Educational variation'})
    v=act(licence,v,'verify');v=act(licence,v,'assess',{'passed':True,'rationale':'Acceptable simulated change'})
    v=act(licence,v,'decide',{'approved':True,'rationale':'Prototype approval'})
    i=create(incident,'/incidents',{'category':'water','location':'Demo site Wollongong',
        'description':'Synthetic water pollution scenario for coursework',
        'observed_at':datetime.now(timezone.utc).isoformat(),'licence_id':licence_id})
    i=act(incident,i,'triage',{'emergency':False,'epa_jurisdiction':True})
    i=act(incident,i,'collect_evidence',{'summary':'Synthetic photo and sample record'})
    i=act(incident,i,'review_licence')
    assert i['data']['licence_context']['licence']['version']==2
    i=act(incident,i,'conclude',{'substantiated':True,'rationale':'Record proposed action for demonstration'})
    result={'mode':'live local HTTP demonstration','licence':{'id':a['id'],'state':a['state']},
            'variation':{'id':v['id'],'state':v['state']},'incident':{'id':i['id'],'state':i['state']},
            'licence_context_version':2,'cross_service_http':True}
    Path('results').mkdir(exist_ok=True)
    Path('results/http_demo.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
