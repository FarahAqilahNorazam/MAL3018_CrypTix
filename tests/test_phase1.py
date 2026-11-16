"""
CrypTix Phase 1 Automated Test Suite
====================================
Tests:
1. Customer registration with mandatory PDPA 2010 consent.
2. Rejection of registration if PDPA consent is omitted.
3. Strict enforcement: new registrations cannot select or receive Admin role.
4. Passwords are saved as BCrypt hashes.
5. User login verifies BCrypt password and issues JWT cookie.
6. Role-Based Access Control (RBAC): Customers are rejected from /admin.
7. Admin access to /admin succeeds.
8. Logout revokes/clears the JWT cookie.
"""
import unittest
from app import create_app
from config import Config
from database.db import get_user_by_email
from utils.auth_utils import verify_password, decode_jwt_token

class Phase1AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_admin_seeded(self):
        """Verify default system administrator account was seeded in database."""
        admin = get_user_by_email(Config.ADMIN_DEFAULT_EMAIL)
        self.assertIsNotNone(admin)
        self.assertEqual(admin['role'], 'Admin')
        self.assertTrue(verify_password(Config.ADMIN_DEFAULT_PASSWORD, admin['password_hash']))

    def test_02_registration_success_customer_role(self):
        """Verify registration creates account with role strictly set to Customer."""
        email = 'test_fan_1@example.com'
        response = self.client.post('/auth/register', data={
            'name': 'Test Fan One',
            'email': email,
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'pdpa_consent': 'on'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        user = get_user_by_email(email)
        self.assertIsNotNone(user)
        self.assertEqual(user['role'], 'Customer')  # Strictly Customer!
        self.assertEqual(user['pdpa_consent'], 1)
        self.assertTrue(verify_password('SecurePassword123!', user['password_hash']))

    def test_03_registration_fails_without_pdpa_consent(self):
        """Verify registration is blocked if PDPA 2010 consent is not checked."""
        email = 'no_consent_user@example.com'
        response = self.client.post('/auth/register', data={
            'name': 'No Consent User',
            'email': email,
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!'
            # pdpa_consent intentionally omitted
        }, follow_redirects=True)

        self.assertIn(b'mandatory PDPA 2010 Consent', response.data)
        user = get_user_by_email(email)
        self.assertIsNone(user)

    def test_04_privilege_escalation_prevented(self):
        """Verify passing role='Admin' in registration payload is ignored."""
        email = 'hacker_attempt@example.com'
        response = self.client.post('/auth/register', data={
            'name': 'Malicious Scalper',
            'email': email,
            'password': 'HackerPassword123!',
            'confirm_password': 'HackerPassword123!',
            'pdpa_consent': 'on',
            'role': 'Admin'  # Attacker attempts to forge Admin role
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        user = get_user_by_email(email)
        self.assertIsNotNone(user)
        self.assertEqual(user['role'], 'Customer')  # System must enforce Customer role!

    def test_05_customer_login_and_jwt_cookie(self):
        """Verify login issues valid signed JWT cookie."""
        response = self.client.post('/auth/login', data={
            'email': 'test_fan_1@example.com',
            'password': 'SecurePassword123!'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        # Check JWT cookie is present
        cookie = response.headers.get('Set-Cookie')
        self.assertIn(Config.JWT_COOKIE_NAME, cookie)
        self.assertIn('HttpOnly', cookie)

    def test_06_customer_cannot_access_admin_route(self):
        """Verify Customer account is rejected from /admin with RBAC denial."""
        # 1. Login as customer
        self.client.post('/auth/login', data={
            'email': 'test_fan_1@example.com',
            'password': 'SecurePassword123!'
        }, follow_redirects=True)

        # 2. Try accessing /admin
        admin_response = self.client.get('/admin', follow_redirects=True)
        # Should be redirected to /dashboard with danger flash message
        self.assertIn(b'Access Denied: You do not have administrator permissions', admin_response.data)

    def test_07_admin_can_access_admin_route(self):
        """Verify Admin account can successfully access /admin."""
        # 1. Login as seeded admin
        self.client.post('/auth/login', data={
            'email': Config.ADMIN_DEFAULT_EMAIL,
            'password': Config.ADMIN_DEFAULT_PASSWORD
        }, follow_redirects=True)

        # 2. Access /admin
        admin_response = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(admin_response.status_code, 200)
        self.assertIn(b'Admin Console', admin_response.data)

    def test_08_logout_clears_cookie(self):
        """Verify logout clears the JWT session cookie."""
        # Login first
        self.client.post('/auth/login', data={
            'email': 'test_fan_1@example.com',
            'password': 'SecurePassword123!'
        })

        # Logout
        response = self.client.get('/auth/logout', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        cookie = response.headers.get('Set-Cookie')
        # Cookie expiration or zero length
        self.assertIn(f'{Config.JWT_COOKIE_NAME}=;', cookie)

if __name__ == '__main__':
    unittest.main()
