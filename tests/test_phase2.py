"""
CrypTix Phase 2 Automated Test Suite
====================================
Tests:
1. Admin can create a new concert event with capacity and price.
2. Non-admin (Customer) cannot create, edit, or delete events (RBAC).
3. Customer can browse all events at /events.
4. Customer can view event details at /events/<id>.
5. Customer can purchase 1-4 tickets via simulated payment.
   - Available capacity decrements.
   - Automatic sequential seat numbers are generated.
6. Customer can view their purchased tickets at /my-tickets.
7. Anti-Scalping Policy 2.1: Enforce maximum 4 tickets per user per event.
   - Attempts to exceed 4 tickets are rejected.
8. Admin can edit and delete events.
"""
import unittest
import uuid
from app import create_app
from config import Config
from database.db import (
    get_all_events, get_event_by_id, get_tickets_by_user_id, 
    get_user_ticket_count_for_event, get_user_by_email
)

class Phase2EventTicketingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Helper: Ensure a unique fresh test fan user exists per test
        self.fan_email = f"test_fan_{uuid.uuid4().hex[:8]}@example.com"
        self.fan_password = "Password123!"
        self.client.get('/auth/logout')
        self.client.post('/auth/register', data={
            'name': 'Phase 2 Test Fan',
            'email': self.fan_email,
            'password': self.fan_password,
            'confirm_password': self.fan_password,
            'pdpa_consent': 'on'
        })
        self.client.get('/auth/logout')
        self.fan_user = get_user_by_email(self.fan_email)

    def login_admin(self):
        self.client.get('/auth/logout')
        return self.client.post('/auth/login', data={
            'email': Config.ADMIN_DEFAULT_EMAIL,
            'password': Config.ADMIN_DEFAULT_PASSWORD
        }, follow_redirects=True)

    def login_fan(self):
        self.client.get('/auth/logout')
        return self.client.post('/auth/login', data={
            'email': self.fan_email,
            'password': self.fan_password
        }, follow_redirects=True)

    def test_01_admin_create_event(self):
        """Verify Admin can create a concert event."""
        self.login_admin()
        response = self.client.post('/admin/events/create', data={
            'event_title': 'Unit Test Concert Live',
            'venue': 'Merdeka Arena, KL',
            'event_date': '2026-12-30 20:00:00',
            'total_capacity': '200',
            'ticket_price': '150.00',
            'description': 'A unit test concert event for automated testing.'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Unit Test Concert Live', response.data)

        # Check DB
        events = get_all_events()
        test_ev = next((e for e in events if e['event_title'] == 'Unit Test Concert Live'), None)
        self.assertIsNotNone(test_ev)
        self.assertEqual(test_ev['total_capacity'], 200)
        self.assertEqual(test_ev['available_capacity'], 200)

    def test_02_customer_cannot_create_event(self):
        """Verify Customer cannot access or create events (RBAC)."""
        self.login_fan()
        # Attempt to access event creation
        response = self.client.get('/admin/events/create', follow_redirects=True)
        self.assertIn(b'Access Denied: You do not have administrator permissions', response.data)

        # Attempt to post event creation
        post_response = self.client.post('/admin/events/create', data={
            'event_title': 'Hacked Concert',
            'venue': 'Hacker Venue',
            'event_date': '2026-12-30 20:00:00',
            'total_capacity': '100',
            'ticket_price': '50.00',
            'description': 'Illegal event'
        }, follow_redirects=True)
        self.assertIn(b'Access Denied: You do not have administrator permissions', post_response.data)

    def test_03_customer_browse_events(self):
        """Verify Customer can browse events."""
        self.login_fan()
        response = self.client.get('/events', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upcoming Concerts', response.data)

    def test_04_customer_view_event_details(self):
        """Verify Customer can view specific event details."""
        self.login_fan()
        events = get_all_events()
        self.assertTrue(len(events) > 0)
        ev_id = events[0]['event_id']

        response = self.client.get(f'/events/{ev_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ticket Checkout', response.data)
        self.assertIn(b'Allowed to Purchase:', response.data)

    def test_05_customer_purchase_tickets_success(self):
        """Verify Customer can purchase tickets and capacity reduces."""
        self.login_fan()
        events = get_all_events()
        ev = events[0]
        ev_id = ev['event_id']
        initial_avail = ev['available_capacity']

        # Purchase 2 tickets
        response = self.client.post(f'/events/{ev_id}/purchase', data={
            'quantity': '2'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Payment Simulated Successfully', response.data)

        # Check DB capacity
        updated_ev = get_event_by_id(ev_id)
        self.assertEqual(updated_ev['available_capacity'], initial_avail - 2)

        # Check user's tickets
        tickets = get_tickets_by_user_id(self.fan_user['user_id'])
        user_ev_tickets = [t for t in tickets if t['event_id'] == ev_id]
        self.assertEqual(len(user_ev_tickets), 2)
        # Check automatic seat number format
        self.assertTrue(user_ev_tickets[0]['seat_number'].startswith('CAT1-A'))

    def test_06_customer_my_tickets_page(self):
        """Verify Customer can see purchased passes on /my-tickets."""
        self.login_fan()
        response = self.client.get('/my-tickets', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Concert Tickets', response.data)

    def test_07_anti_scalping_max_4_tickets_limit(self):
        """Verify Anti-Scalping Policy: Rejects purchases exceeding 4 tickets per user per event."""
        # 1. Login as Admin to create a clean event
        self.login_admin()
        create_resp = self.client.post('/admin/events/create', data={
            'event_title': 'Anti-Scalping Test Tour',
            'venue': 'Test Stadium',
            'event_date': '2027-02-01 20:00:00',
            'total_capacity': '100',
            'ticket_price': '100.00',
            'description': 'Testing 4-ticket limit'
        }, follow_redirects=True)
        self.assertEqual(create_resp.status_code, 200)

        events = get_all_events()
        test_ev = next(e for e in events if e['event_title'] == 'Anti-Scalping Test Tour')
        ev_id = test_ev['event_id']

        # 2. Login as Fan
        self.login_fan()

        # Step 1: Buy 3 tickets (valid: 3 <= 4)
        resp1 = self.client.post(f'/events/{ev_id}/purchase', data={'quantity': '3'}, follow_redirects=True)
        self.assertIn(b'Payment Simulated Successfully', resp1.data)
        self.assertEqual(get_user_ticket_count_for_event(self.fan_user['user_id'], ev_id), 3)

        # Step 2: Try to buy 2 more tickets (3 + 2 = 5 > 4: MUST FAIL!)
        resp2 = self.client.post(f'/events/{ev_id}/purchase', data={'quantity': '2'}, follow_redirects=True)
        self.assertIn(b'Anti-Scalping Rule Violation: Maximum 4 tickets per user', resp2.data)
        self.assertEqual(get_user_ticket_count_for_event(self.fan_user['user_id'], ev_id), 3)

        # Step 3: Buy 1 more ticket (3 + 1 = 4 <= 4: MUST SUCCEED!)
        resp3 = self.client.post(f'/events/{ev_id}/purchase', data={'quantity': '1'}, follow_redirects=True)
        self.assertIn(b'Payment Simulated Successfully', resp3.data)
        self.assertEqual(get_user_ticket_count_for_event(self.fan_user['user_id'], ev_id), 4)

        # Step 4: Try to buy 1 more ticket (4 + 1 = 5 > 4: MUST FAIL!)
        resp4 = self.client.post(f'/events/{ev_id}/purchase', data={'quantity': '1'}, follow_redirects=True)
        self.assertIn(b'Anti-Scalping Rule Violation: Maximum 4 tickets per user', resp4.data)
        self.assertEqual(get_user_ticket_count_for_event(self.fan_user['user_id'], ev_id), 4)

    def test_08_admin_edit_and_delete_event(self):
        """Verify Admin can edit and delete events."""
        self.login_admin()
        # Create event to edit
        self.client.post('/admin/events/create', data={
            'event_title': 'Event To Edit',
            'venue': 'Old Venue',
            'event_date': '2026-11-15 19:00:00',
            'total_capacity': '50',
            'ticket_price': '80.00',
            'description': 'Before edit'
        })
        events = get_all_events()
        ev = next(e for e in events if e['event_title'] == 'Event To Edit')
        ev_id = ev['event_id']

        # Edit event
        edit_resp = self.client.post(f'/admin/events/{ev_id}/edit', data={
            'event_title': 'Event Edited Title',
            'venue': 'New Arena Venue',
            'event_date': '2026-11-20 20:00:00',
            'total_capacity': '100',
            'ticket_price': '95.00',
            'description': 'After edit'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        updated_ev = get_event_by_id(ev_id)
        self.assertEqual(updated_ev['event_title'], 'Event Edited Title')
        self.assertEqual(updated_ev['venue'], 'New Arena Venue')

        # Delete event
        del_resp = self.client.post(f'/admin/events/{ev_id}/delete', follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertIsNone(get_event_by_id(ev_id))

if __name__ == '__main__':
    unittest.main()
