import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import HTTPException
from services.licensing import create_app as licence_app
from services.incidents import create_app as incident_app

C={'Authorization':'Bearer demo-client-token'}
O={'Authorization':'Bearer demo-officer-token'}
OTHER={'Authorization':'Bearer demo-other-token'}

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.clock=datetime(2026,1,1,tzinfo=timezone.utc)
        self.lapp=licence_app(self.root/'licence.sqlite',lambda:self.clock)
        self.l=TestClient(self.lapp)
        self.i=TestClient(incident_app(self.root/'incident.sqlite',
            context_loader=lambda key:{'summary':'Test lookup','licence':self.lapp.state.store.get_licence(key)}))

    def application(self,key='a',**overrides):
        data={'applicant':'Demo Pty Ltd','premises':'Demo site','activity':'Resource recovery',
              'documents':['plan.pdf'],'fee_reference':'DEMO','consent_reference':'DEMO'}
        data.update(overrides)
        r=self.l.post('/applications',headers={**C,'Idempotency-Key':key},json=data)
        self.assertEqual(r.status_code,201,r.text);return r.json()

    def action(self,client,case,action,values=None,headers=O,expected=200):
        r=client.post('/cases/'+case['id']+'/commands',headers=headers,
            json={'expected_version':case['version'],'action':action,'values':values or {}})
        self.assertEqual(r.status_code,expected,r.text);return r.json()

    def approved(self,key='a'):
        a=self.application(key);a=self.action(self.l,a,'check')
        for step in ('assess_environment','assess_suitability'):
            a=self.action(self.l,a,step,{'passed':True,'rationale':'Demo passed'})
        return self.action(self.l,a,'decide',{'approved':True,'rationale':'Demo approval'})

    def report(self,key='r',licence_id=None):
        r=self.i.post('/incidents',headers={**C,'Idempotency-Key':key},json={
            'category':'water','location':'Demo site','description':'Synthetic pollution observation',
            'observed_at':'2026-01-01T01:00:00Z','licence_id':licence_id})
        self.assertEqual(r.status_code,201,r.text);return r.json()

    def test_unauthorised_requests(self):
        self.assertEqual(self.l.get('/events').status_code,401)
        self.assertEqual(self.l.get('/events',headers=C).status_code,403)

    def test_ownership_and_officer_boundaries(self):
        a=self.application()
        self.assertEqual(self.l.get('/cases/'+a['id'],headers=OTHER).status_code,403)
        self.action(self.l,a,'check',headers=C,expected=403)

    def test_idempotent_creation_and_conflict(self):
        a=self.application();b=self.application();self.assertEqual(a['id'],b['id'])
        self.assertEqual(len(self.lapp.state.store.events()),1)
        r=self.l.post('/applications',headers={**C,'Idempotency-Key':'a'},json={
            'applicant':'Different applicant','premises':'Demo site','activity':'Resource recovery'})
        self.assertEqual(r.status_code,409)

    def test_both_parallel_checks_required(self):
        a=self.application();a=self.action(self.l,a,'check')
        a=self.action(self.l,a,'assess_environment',{'passed':True,'rationale':'Demo'})
        self.action(self.l,a,'decide',{'approved':True,'rationale':'Too early'},expected=409)
        self.assertNotIn('A9',[e['task_id'] for e in self.lapp.state.store.events()])

    def test_failed_check_prevents_approval(self):
        a=self.application();a=self.action(self.l,a,'check')
        for step in ('assess_environment','assess_suitability'):
            a=self.action(self.l,a,step,{'passed':False,'rationale':'Demo failed'})
        self.action(self.l,a,'decide',{'approved':True,'rationale':'Invalid approval'},expected=409)
        a=self.action(self.l,a,'decide',{'approved':False,'rationale':'Failure recorded'})
        self.assertEqual(a['state'],'REFUSED')

    def test_stale_update_and_no_duplicate_event(self):
        a=self.application();self.action(self.l,a,'check')
        count=len(self.lapp.state.store.events())
        self.action(self.l,a,'check',expected=409)
        self.assertEqual(count,len(self.lapp.state.store.events()))

    def test_information_loop_and_timer(self):
        a=self.application(documents=[]);a=self.action(self.l,a,'check')
        self.action(self.l,a,'expire',{'rationale':'Too early'},expected=409)
        a=self.action(self.l,a,'supply',{'documents':['plan.pdf']},headers=C)
        a=self.action(self.l,a,'check');self.assertEqual(a['state'],'ASSESSMENT')
        b=self.application(key='b',documents=[]);b=self.action(self.l,b,'check')
        self.clock+=timedelta(days=31)
        self.action(self.l,b,'supply',{'documents':['late-plan.pdf']},headers=C,expected=409)
        b=self.action(self.l,b,'expire',{'rationale':'Prototype timer elapsed'})
        self.assertEqual(b['state'],'INCOMPLETE_CLOSED')
        self.assertNotIn('information_due_at',b['data'])

    def test_variation_updates_owned_licence(self):
        a=self.approved();lid=a['data']['licence_id']
        payload={'licence_id':lid,'proposed_conditions':['Updated demo condition'],'rationale':'Demo change'}
        r=self.l.post('/variations',headers={**OTHER,'Idempotency-Key':'v'},json=payload)
        self.assertEqual(r.status_code,403)
        v=self.l.post('/variations',headers={**C,'Idempotency-Key':'v'},json=payload).json()
        v=self.action(self.l,v,'verify');v=self.action(self.l,v,'assess',{'passed':True,'rationale':'Demo'})
        v=self.action(self.l,v,'decide',{'approved':True,'rationale':'Demo'})
        self.assertEqual(self.l.get('/licences/'+lid,headers=C).json()['version'],2)
        replay=self.l.post('/variations',headers={**C,'Idempotency-Key':'v'},json=payload)
        self.assertEqual(replay.status_code,201);self.assertEqual(replay.json()['id'],v['id'])

    def test_incident_composition_and_join(self):
        lid=self.approved()['data']['licence_id'];i=self.report(licence_id=lid)
        i=self.action(self.i,i,'triage',{'emergency':False,'epa_jurisdiction':True})
        i=self.action(self.i,i,'review_licence')
        self.action(self.i,i,'conclude',{'substantiated':True,'rationale':'Too early'},expected=409)
        i=self.action(self.i,i,'collect_evidence',{'summary':'Demo evidence'})
        i=self.action(self.i,i,'conclude',{'substantiated':True,'rationale':'Demo conclusion'})
        self.assertEqual(i['state'],'ACTION_RECORDED')

    def test_emergency_and_referral_do_not_start_investigation(self):
        for key,emergency,jurisdiction,state in [('e',True,True,'EMERGENCY_GUIDANCE'),('f',False,False,'REFERRED')]:
            i=self.report(key)
            i=self.action(self.i,i,'triage',{'emergency':emergency,'epa_jurisdiction':jurisdiction})
            self.assertEqual(i['state'],state)
            self.action(self.i,i,'collect_evidence',{'summary':'Not permitted'},expected=409)

    def test_lookup_failure_preserves_case_and_version(self):
        def fail(_):raise HTTPException(503,'Simulated lookup outage')
        client=TestClient(incident_app(self.root/'outage.sqlite',context_loader=fail))
        r=client.post('/incidents',headers={**C,'Idempotency-Key':'outage'},json={
            'category':'water','location':'Demo site','description':'Synthetic test incident',
            'observed_at':'2026-01-01T01:00:00Z','licence_id':'NZ-DEMO'}).json()
        r=self.action(client,r,'triage',{'emergency':False,'epa_jurisdiction':True})
        self.action(client,r,'review_licence',expected=503)
        current=client.get('/cases/'+r['id'],headers=C).json()
        self.assertEqual(current['version'],r['version']);self.assertNotIn('licence_context',current['data'])

    def test_persistence_and_input_validation(self):
        a=self.approved()
        restarted=TestClient(licence_app(self.root/'licence.sqlite'))
        self.assertEqual(restarted.get('/cases/'+a['id'],headers=C).json()['state'],'APPROVED')
        bad=self.i.post('/incidents',headers={**C,'Idempotency-Key':'bad'},json={
            'category':'water','location':'Demo site','description':'Synthetic test incident','observed_at':'2026-01-01T01:00:00'})
        self.assertEqual(bad.status_code,422)

if __name__=='__main__':unittest.main(verbosity=2)
