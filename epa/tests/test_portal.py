import os
import tempfile
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from services.licensing import create_app
from services.incidents import create_app as incident_app
from services.portal import verified_principal, create_licensing_app


class PortalAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'NZ_AUTH_URL': 'http://identity.test/api/v1/auth/me/',
                                     'NZ_INTERNAL_TOKEN': 'test-internal-credential'})
        env.start()
        self.addCleanup(env.stop)
        self.response = patch('services.portal.httpx.get', side_effect=self.identity)
        self.mock = self.response.start()
        self.addCleanup(self.response.stop)
        self.client = TestClient(create_app(self.tmp.name + '/licensing.sqlite', identity_dependency=verified_principal))
        self.incidents = TestClient(incident_app(self.tmp.name + '/incidents.sqlite', identity_dependency=verified_principal))

    @staticmethod
    def identity(url, *, headers, **kwargs):
        users = {'Token alice': (1, 'client'), 'Token bob': (2, 'client'), 'Token officer': (3, 'officer')}
        user = users.get(headers['Authorization'])
        if user is None:
            return httpx.Response(401, json={'detail': 'Invalid token'})
        return httpx.Response(200, json={'id': user[0], 'epa_role': user[1], 'full_name': 'Portal user'})

    def test_shared_identity_is_accepted_by_both_services(self):
        for client in (self.client, self.incidents):
            response = client.get('/me', headers={'Authorization': 'Token alice'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['subject'], 'django:1')

    def test_demo_tokens_and_missing_or_invalid_tokens_are_rejected(self):
        for value in ('', 'Bearer demo-client-token', 'Bearer demo-officer-token', 'Token unknown', 'Token a b'):
            self.assertEqual(self.client.get('/cases', headers={'Authorization': value}).status_code, 401)

    def test_case_ownership_and_officer_access(self):
        result = self.client.post('/applications', json={'applicant': 'Alice', 'premises': 'Test site', 'activity': 'Testing'},
                                  headers={'Authorization': 'Token alice', 'Idempotency-Key': 'alice-application'})
        self.assertEqual(result.status_code, 201)
        case = result.json()
        self.assertEqual(case['owner'], 'django:1')
        self.assertEqual(self.client.get('/cases', headers={'Authorization': 'Token bob'}).json(), [])
        self.assertEqual(self.client.get('/cases/' + case['id'], headers={'Authorization': 'Token bob'}).status_code, 403)
        self.assertEqual(self.client.get('/cases/' + case['id'], headers={'Authorization': 'Token officer'}).status_code, 200)
        self.assertEqual(self.client.get('/events', headers={'Authorization': 'Token alice'}).status_code, 403)

    def test_authentication_outage_fails_closed(self):
        self.mock.side_effect = httpx.ConnectError('offline')
        self.assertEqual(self.client.get('/cases', headers={'Authorization': 'Token alice'}).status_code, 503)

    def test_invalid_identity_response_fails_closed(self):
        self.mock.side_effect = None
        for payload in ({'id': 1}, {'id': True, 'epa_role': 'officer'}, {'id': 1, 'epa_role': 'internal'}):
            self.mock.return_value = httpx.Response(200, json=payload)
            self.assertEqual(self.client.get('/cases', headers={'Authorization': 'Token alice'}).status_code, 503)

    def test_revoked_token_is_not_cached(self):
        headers = {'Authorization': 'Token alice'}
        self.assertEqual(self.client.get('/cases', headers=headers).status_code, 200)
        self.mock.side_effect = None
        self.mock.return_value = httpx.Response(401, json={'detail': 'Invalid token'})
        self.assertEqual(self.client.get('/cases', headers=headers).status_code, 401)

    def test_internal_credential_cannot_access_user_or_event_endpoints(self):
        headers = {'Authorization': 'Bearer test-internal-credential'}
        self.assertEqual(self.client.get('/internal/licences/nonexistent/context', headers=headers).status_code, 404)
        for path in ('/me', '/cases', '/events', '/events/export'):
            self.assertEqual(self.client.get(path, headers=headers).status_code, 403)

    def test_portal_factory_requires_identity_configuration(self):
        with patch.dict(os.environ, {'NZ_AUTH_URL': ''}):
            with self.assertRaises(RuntimeError):
                create_licensing_app()
