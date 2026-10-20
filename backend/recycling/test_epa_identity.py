from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class EpaIdentityTests(APITestCase):
    def identity(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return self.client.get('/api/v1/auth/me/', HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_resident_and_general_provider_staff_are_epa_clients(self):
        for staff in (False, True):
            user = get_user_model().objects.create_user(f'user-{staff}', password='Test927!Local', is_staff=staff)
            response = self.identity(user)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['epa_role'], 'client')

    def test_epa_group_and_superuser_have_officer_access(self):
        officer = get_user_model().objects.create_user('epa-officer', password='Test927!Local')
        officer.groups.add(Group.objects.create(name='EPA Officers'))
        admin = get_user_model().objects.create_superuser('hub-admin', password='Test927!Local')
        for user in (officer, admin):
            self.assertEqual(self.identity(user).data['epa_role'], 'officer')

    def test_registration_cannot_grant_officer_privileges(self):
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'new-resident', 'email': 'new@example.com', 'password': 'Test927!Local',
            'epa_role': 'officer', 'is_staff': True, 'is_superuser': True,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['epa_role'], 'client')
        self.assertFalse(response.data['user']['is_staff'])

    def test_logout_revokes_identity_token(self):
        user = get_user_model().objects.create_user('logout-user', password='Test927!Local')
        token = Token.objects.create(user=user)
        auth = {'HTTP_AUTHORIZATION': f'Token {token.key}'}
        self.assertEqual(self.client.post('/api/v1/auth/logout/', **auth).status_code, 204)
        self.assertEqual(self.client.get('/api/v1/auth/me/', **auth).status_code, 401)
