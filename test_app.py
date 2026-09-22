import unittest
import os
import json
from app import create_app
from database import query_db, execute_db, init_db, haversine
from seed_data import seed_database
from config import Config

class LocalServeTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Seed test database
        with self.app.app_context():
            seed_database()

    def test_database_seeded(self):
        """Verify initial database tables and data seeding."""
        with self.app.app_context():
            users = query_db("SELECT COUNT(*) as c FROM users", one=True)
            self.assertGreater(users['c'], 0)
            
            providers = query_db("SELECT COUNT(*) as c FROM providers", one=True)
            self.assertGreater(providers['c'], 0)
            
            medicines = query_db("SELECT COUNT(*) as c FROM medicines", one=True)
            self.assertGreater(medicines['c'], 0)

            inventory = query_db("SELECT COUNT(*) as c FROM medicine_inventory", one=True)
            self.assertGreater(inventory['c'], 0)

    def test_haversine_distance(self):
        """Verify Haversine distance calculation."""
        # Distance between two nearby points in Hyderabad (~1 km apart)
        dist = haversine(17.3850, 78.4867, 17.3910, 78.4910)
        self.assertGreater(dist, 0.5)
        self.assertLess(dist, 2.0)

    def test_homepage_and_services(self):
        """Verify homepage and services rendering."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Gramin Quick-Assist', response.data)
        self.assertIn(b'LOCALServe', response.data)

        # Services search
        serv_resp = self.client.get('/services?category=Electrician&radius=15')
        self.assertEqual(serv_resp.status_code, 200)
        self.assertIn(b'Ramesh Electrician', serv_resp.data)

    def test_quick_login_and_roles(self):
        """Verify 1-click demo login for all roles."""
        # Customer login
        res = self.client.get('/quick-login/customer', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Venkata Rao', res.data)

        # Provider login
        res = self.client.get('/quick-login/provider', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Provider Dashboard', res.data)

        # Pharmacy login
        res = self.client.get('/quick-login/pharmacy', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Pharmacy Dashboard', res.data)

        # Admin login
        res = self.client.get('/quick-login/admin', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'LOCALServe Platform Administration', res.data)

    def test_medicine_search_and_availability(self):
        """Verify medicine search shows pharmacy-reported status and timestamps."""
        res = self.client.get('/medicines?q=Paracetamol')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Paracetamol 500mg', res.data)
        self.assertIn(b'Available', res.data)
        self.assertIn(b'Balaji Medical', res.data)

    def test_medicine_request_community_broadcast(self):
        """Verify patient can broadcast a medicine request and pharmacy can respond."""
        # Login customer
        self.client.get('/quick-login/customer')

        # Broadcast request
        req_res = self.client.post('/medicine-request', data={
            'medicine_name': 'Nebulizer Solution',
            'strength': '2.5mg',
            'quantity': '1 box',
            'customer_phone': '+91 9876543210',
            'address': 'Farmhouse Road, Block 2'
        }, follow_redirects=True)
        self.assertEqual(req_res.status_code, 200)

        with self.app.app_context():
            req = query_db("SELECT * FROM medicine_requests WHERE medicine_name = 'Nebulizer Solution'", one=True)
            self.assertIsNotNone(req)
            req_id = req['request_id']

        # Now login pharmacy and respond
        self.client.get('/quick-login/pharmacy')
        resp_res = self.client.post(f'/pharmacy/request/{req_id}/respond', data={
            'response_status': 'Available',
            'notes': 'Available in stock for Rs 120 per box'
        }, follow_redirects=True)
        self.assertEqual(resp_res.status_code, 200)

        with self.app.app_context():
            resp = query_db("SELECT * FROM pharmacy_responses WHERE request_id = ?", (req_id,), one=True)
            self.assertIsNotNone(resp)
            self.assertEqual(resp['response_status'], 'Available')

    def test_booking_lifecycle_and_review(self):
        """Verify complete booking flow: Request -> Accept -> Progress -> Complete -> Review."""
        # 1. Customer creates booking
        self.client.get('/quick-login/customer')
        with self.app.app_context():
            provider = query_db("SELECT provider_id FROM providers LIMIT 1", one=True)
            pid = provider['provider_id']

        book_res = self.client.post(f'/book/{pid}', data={
            'booking_date': '2026-09-25',
            'booking_time': 'Morning (8:00 AM - 12:00 PM)',
            'description': 'Ceiling fan burning smell and regulator spark',
            'customer_name': 'Venkata Rao',
            'customer_phone': '+91 9876543210',
            'address': 'House 4-21, Gandhi Nagar'
        }, follow_redirects=True)
        self.assertEqual(book_res.status_code, 200)

        with self.app.app_context():
            booking = query_db("SELECT * FROM bookings WHERE description LIKE '%burning smell%'", one=True)
            self.assertIsNotNone(booking)
            bid = booking['booking_id']
            self.assertEqual(booking['status'], 'Requested')

        # 2. Provider accepts booking
        self.client.get('/quick-login/provider')
        accept_res = self.client.post(f'/provider/booking/{bid}/respond', data={'action': 'accept'}, follow_redirects=True)
        self.assertEqual(accept_res.status_code, 200)

        # 3. Provider advances through stages
        self.client.post(f'/provider/booking/{bid}/status', data={'status': 'On the Way'}, follow_redirects=True)
        self.client.post(f'/provider/booking/{bid}/status', data={'status': 'Service Started'}, follow_redirects=True)
        self.client.post(f'/provider/booking/{bid}/status', data={'status': 'Completed'}, follow_redirects=True)

        with self.app.app_context():
            b_updated = query_db("SELECT status FROM bookings WHERE booking_id = ?", (bid,), one=True)
            self.assertEqual(b_updated['status'], 'Completed')

        # 4. Customer submits 5-star review
        self.client.get('/quick-login/customer')
        rev_res = self.client.post(f'/review/{bid}', data={
            'rating': '5',
            'comment': 'Solved fan issue in 15 minutes, great service!'
        }, follow_redirects=True)
        self.assertEqual(rev_res.status_code, 200)

        with self.app.app_context():
            rev = query_db("SELECT * FROM reviews WHERE booking_id = ?", (bid,), one=True)
            self.assertIsNotNone(rev)
            self.assertEqual(rev['rating'], 5)

    def test_rest_apis(self):
        """Verify REST APIs for nearby providers and medicines."""
        # Nearby providers API
        api_res = self.client.get('/api/providers/nearby?lat=17.3850&lng=78.4867&radius=20')
        self.assertEqual(api_res.status_code, 200)
        data = json.loads(api_res.data)
        self.assertIn('providers', data)
        self.assertGreater(data['count'], 0)

        # Medicine search API
        med_res = self.client.get('/api/medicines/search?q=ORS')
        self.assertEqual(med_res.status_code, 200)
        mdata = json.loads(med_res.data)
        self.assertIn('medicines', mdata)
        self.assertGreater(mdata['count'], 0)

if __name__ == '__main__':
    unittest.main()
