"""New API behaviour required by the React module."""
import csv
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from fastapi.testclient import TestClient
from services.licensing import create_app
from services.incidents import create_app as incident_app

C = {'Authorization': 'Bearer demo-client-token'}
O = {'Authorization': 'Bearer demo-officer-token'}
OTHER = {'Authorization': 'Bearer demo-other-token'}
INTERNAL = {'Authorization': 'Bearer demo-internal-token'}

class FrontendApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.client = TestClient(create_app(Path(self.tmp.name) / 'licensing.sqlite'))
        self.case = self.client.post('/applications', headers={**C, 'Idempotency-Key': 'first'}, json={
            'applicant': 'Demo company', 'premises': 'Sample location', 'activity': 'Resource recovery'}).json()

    def test_case_lists_and_histories_enforce_ownership(self):
        self.assertEqual(len(self.client.get('/cases', headers=C).json()), 1)
        self.assertEqual(self.client.get('/cases', headers=OTHER).json(), [])
        self.assertEqual(len(self.client.get('/cases', headers=O).json()), 1)
        path = '/cases/' + self.case['id'] + '/events'
        self.assertEqual(self.client.get(path, headers=OTHER).status_code, 403)
        self.assertEqual(self.client.get(path, headers=C).json()[0]['task_id'], 'A1')
        self.assertEqual(self.client.get('/cases', headers=INTERNAL).status_code, 403)

    def test_export_formats_and_permissions(self):
        self.assertEqual(self.client.get('/events/export', headers=C).status_code, 403)
        result = self.client.get('/events/export?format=csv', headers=O)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(list(csv.DictReader(io.StringIO(result.text)))[0]['case_id'], self.case['id'])
        xes = self.client.get('/events/export?format=xes', headers=O)
        root = ET.fromstring(xes.content)
        self.assertEqual(len(root.findall('{http://www.xes-standard.org/}trace')), 1)
        self.assertEqual(self.client.get('/events/export?format=invalid', headers=O).status_code, 422)

    def test_invalid_commands_do_not_modify_data(self):
        case = self.client.post('/cases/' + self.case['id'] + '/commands', headers=O,
            json={'action': 'check', 'expected_version': 1}).json()
        result = self.client.post('/cases/' + case['id'] + '/commands', headers=C,
            json={'action': 'supply', 'expected_version': case['version'], 'values': {'documents': 'not-a-list'}})
        self.assertEqual(result.status_code, 422)
        saved = self.client.get('/cases/' + case['id'], headers=C).json()
        self.assertEqual(saved['version'], case['version'])
        self.assertEqual(saved['data']['documents'], [])

    def test_empty_references_and_names_are_rejected(self):
        for changes in [{'applicant': '   '}, {'documents': ['   ']}]:
            result = self.client.post('/applications', headers={**C, 'Idempotency-Key': 'invalid'}, json={
                'applicant': 'Demo company', 'premises': 'Sample location', 'activity': 'Resource recovery', **changes})
            self.assertEqual(result.status_code, 422)

    def test_me_and_licence_listing_are_authorised(self):
        self.assertEqual(self.client.get('/me', headers=O).json()['role'], 'officer')
        self.assertEqual(self.client.get('/me').status_code, 401)
        self.assertEqual(self.client.get('/licences', headers=C).json(), [])
        self.assertEqual(self.client.get('/licences', headers=INTERNAL).status_code, 403)

    def test_group_identity_dependency_sets_stable_record_owner(self):
        def verified_group_user():
            return {'subject': 'group-user-123', 'role': 'client'}
        api = TestClient(create_app(Path(self.tmp.name) / 'group.sqlite', identity_dependency=verified_group_user))
        self.assertEqual(api.get('/me').json()['subject'], 'group-user-123')
        response = api.post('/applications', headers={'Idempotency-Key': 'group'}, json={
            'applicant': 'Group member', 'premises': 'Synthetic location', 'activity': 'Synthetic activity'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['owner'], 'group-user-123')

    def test_incident_read_api_and_boolean_validation(self):
        api = TestClient(incident_app(Path(self.tmp.name) / 'incidents.sqlite'))
        item = api.post('/incidents', headers={**C, 'Idempotency-Key': 'incident'}, json={
            'category': 'water', 'location': 'Sample site', 'description': 'Demonstration observation',
            'observed_at': '2026-10-01T10:00:00Z'}).json()
        self.assertEqual(api.get('/cases', headers=OTHER).json(), [])
        self.assertEqual(len(api.get('/cases', headers=C).json()), 1)
        result = api.post('/cases/' + item['id'] + '/commands', headers=O, json={
            'action': 'triage', 'expected_version': 1, 'values': {'emergency': 'false', 'epa_jurisdiction': True}})
        self.assertEqual(result.status_code, 422)

if __name__ == '__main__':
    unittest.main(verbosity=2)
