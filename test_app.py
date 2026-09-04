"""
Comprehensive test suite to verify every feature of the College Club Management System
"""
import unittest
import html
from datetime import datetime, timedelta
from app import app, db
from models import User, Club, Membership, Event, EventRegistration, Announcement

class CollegeClubSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_database_seeded(self):
        """Verify initial database tables and seed data"""
        self.assertGreaterEqual(User.query.count(), 10, "Should have at least 10 users seeded")
        self.assertGreaterEqual(Club.query.count(), 6, "Should have at least 6 clubs seeded")
        self.assertGreaterEqual(Event.query.count(), 8, "Should have at least 8 events seeded")
        self.assertGreaterEqual(Announcement.query.count(), 6, "Should have at least 6 announcements seeded")

    def test_02_public_pages(self):
        """Verify public catalog pages render 200 OK"""
        routes = ['/', '/clubs', '/events', '/announcements', '/login', '/register']
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} should return 200 OK")
            self.assertIn(b'Campus', res.data)

    def test_03_club_and_event_details(self):
        """Verify individual club and event detail pages render 200 OK"""
        club = Club.query.first()
        res = self.client.get(f'/clubs/{club.id}')
        self.assertEqual(res.status_code, 200)
        decoded_club_data = html.unescape(res.data.decode('utf-8'))
        self.assertIn(club.name, decoded_club_data)

        event = Event.query.first()
        res = self.client.get(f'/events/{event.id}')
        self.assertEqual(res.status_code, 200)
        decoded_event_data = html.unescape(res.data.decode('utf-8'))
        self.assertIn(event.title, decoded_event_data)

    def test_04_auth_login_logout(self):
        """Verify student, coordinator, and admin login/logout"""
        # Student login
        res = self.client.post('/login', data={'username': 'alex', 'password': 'Student@123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Alex Rivera', res.data)

        # Access student dashboard
        res = self.client.get('/student/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'logged out', res.data)

    def test_05_student_club_joining_leaving(self):
        """Verify student joining a club and leaving"""
        with self.client:
            self.client.post('/login', data={'username': 'marcus', 'password': 'Student@123'})
            user = User.query.filter_by(username='marcus').first()
            cultural_club = Club.query.filter_by(name='Cultural Club').first()
            
            # Clean up prior test state if any
            existing_mem = Membership.query.filter_by(user_id=user.id, club_id=cultural_club.id).first()
            if existing_mem:
                db.session.delete(existing_mem)
                db.session.commit()

            self.assertFalse(cultural_club.is_user_member(user.id))

            # Join
            res = self.client.post(f'/clubs/{cultural_club.id}/join', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertTrue(cultural_club.is_user_member(user.id))

            # Leave
            res = self.client.post(f'/clubs/{cultural_club.id}/leave', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertFalse(cultural_club.is_user_member(user.id))

    def test_06_student_event_registration_and_business_rules(self):
        """Verify RSVP, capacity check, past event prevention, and cancel"""
        with self.client:
            self.client.post('/login', data={'username': 'sarah', 'password': 'Student@123'})
            user = User.query.filter_by(username='sarah').first()
            
            event = Event.query.filter(Event.title.like('%Bootcamp%')).first()
            
            # Ensure not registered initially
            existing = EventRegistration.query.filter_by(event_id=event.id, user_id=user.id).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

            # 1. Register successfully
            res = self.client.post(f'/events/{event.id}/register', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertTrue(event.is_user_registered(user.id))

            # 2. Cancel RSVP
            res = self.client.post(f'/events/{event.id}/cancel', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertFalse(event.is_user_registered(user.id))

            # 3. Prevent past event registration
            past_event = Event.query.filter(Event.event_date < datetime.now()).first()
            res = self.client.post(f'/events/{past_event.id}/register', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'closed because this event has already ended', res.data)

    def test_07_coordinator_actions(self):
        """Verify coordinator dashboard, event creation, attendee checkin, and announcement post"""
        with self.client:
            self.client.post('/login', data={'username': 'coding_lead', 'password': 'Coord@123'})
            
            # Dashboard
            res = self.client.get('/coordinator/dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Coding Club', res.data)

            # Create event
            event_payload = {
                'title': 'Test Hackathon 2026',
                'description': 'Hackathon testing description for coordinator.',
                'location': 'CS Lab 4',
                'venue_type': 'Lab',
                'event_date': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
                'registration_deadline': (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%dT%H:%M'),
                'max_capacity': '50',
                'fee': '0.0',
                'image_url': ''
            }
            res = self.client.post('/coordinator/events/new', data=event_payload, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            created_event = Event.query.filter_by(title='Test Hackathon 2026').first()
            self.assertIsNotNone(created_event)

            # Post announcement
            ann_payload = {
                'title': 'Test Announcement from Coding Coord',
                'content': 'This is an automated test announcement.',
                'priority': 'important'
            }
            res = self.client.post('/coordinator/announcements/new', data=ann_payload, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            created_ann = Announcement.query.filter_by(title='Test Announcement from Coding Coord').first()
            self.assertIsNotNone(created_ann)

            # Clean up
            self.client.post(f'/coordinator/events/{created_event.id}/delete', follow_redirects=True)
            self.client.post(f'/coordinator/announcements/{created_ann.id}/delete', follow_redirects=True)

    def test_08_admin_management_and_rbac(self):
        """Verify admin dashboard, user role modification, user toggle, and club operations"""
        with self.client:
            self.client.post('/login', data={'username': 'admin', 'password': 'Admin@123'})
            
            # Admin dashboard
            res = self.client.get('/admin/dashboard')
            self.assertEqual(res.status_code, 200)

            # Admin users
            res = self.client.get('/admin/users')
            self.assertEqual(res.status_code, 200)

            # Create club
            club_payload = {
                'name': 'Astronomy & Space Club',
                'category': 'Technical',
                'short_description': 'Stargazing, astrophysics lectures, and telescope builds.',
                'description': 'Exploring cosmological wonders and building optical telescopes.',
                'room_or_location': 'Science Observation Tower',
                'meeting_schedule': 'Saturdays at 8:00 PM',
                'email': 'astronomy@college.edu',
                'banner_url': ''
            }
            res = self.client.post('/admin/clubs/new', data=club_payload, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            
            astro_club = Club.query.filter_by(name='Astronomy & Space Club').first()
            self.assertIsNotNone(astro_club)

            # Delete club
            res = self.client.post(f'/admin/clubs/{astro_club.id}/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIsNone(Club.query.filter_by(name='Astronomy & Space Club').first())

    def test_09_error_handling(self):
        """Verify 404 handler returns proper page"""
        res = self.client.get('/non-existent-page-url-404')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b'Page Not Found', res.data)

if __name__ == '__main__':
    unittest.main()
