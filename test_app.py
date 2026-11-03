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
        # Distance between two nearby points in Gudlavalleru (~0.72 km apart)
        dist = haversine(16.3486, 81.0442, 16.3540, 81.0480)
        self.assertGreater(dist, 0.5)
        self.assertLess(dist, 2.0)

    def test_homepage_and_services(self):
        """Verify homepage and services rendering."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Gramin Quick-Assist', response.data)
        self.assertIn(b'SevaSetu', response.data)

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
        self.assertIn(b'SevaSetu Platform Administration', res.data)

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
            'address': 'House No. 2-45, Gandhi Bomma Street, Gudlavalleru - 521356'
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
        api_res = self.client.get('/api/providers/nearby?lat=16.3486&lng=81.0442&radius=20')
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

    def test_skillshare_hub_and_courses(self):
        """Verify SkillShare Hub, course catalog, and syllabus views."""
        # 1. Hub
        hub_res = self.client.get('/skillshare/')
        self.assertEqual(hub_res.status_code, 200)
        self.assertIn(b'SkillShare', hub_res.data)
        self.assertIn(b'People Trained', hub_res.data)

        # 2. Courses list
        c_res = self.client.get('/skillshare/courses')
        self.assertEqual(c_res.status_code, 200)
        self.assertIn(b'Household Electrical', c_res.data)

        # 3. Course detail
        with self.app.app_context():
            course = query_db("SELECT course_id FROM courses LIMIT 1", one=True)
            cid = course['course_id']

        cd_res = self.client.get(f'/skillshare/course/{cid}')
        self.assertEqual(cd_res.status_code, 200)
        self.assertIn(b'Mandatory Safety Precautions', cd_res.data)
        self.assertIn(b'Practical Hands-on Syllabus', cd_res.data)

    def test_course_enrollment_and_certificate(self):
        """Verify learner can enroll, complete lessons, and unlock verifiable certificate."""
        self.client.get('/quick-login/customer')

        with self.app.app_context():
            course = query_db("SELECT course_id FROM courses WHERE title LIKE '%Plumbing%'", one=True)
            cid = course['course_id']

        # Enroll
        enroll_res = self.client.post(f'/skillshare/course/{cid}/enroll', follow_redirects=True)
        self.assertEqual(enroll_res.status_code, 200)

        with self.app.app_context():
            u = query_db("SELECT user_id FROM users WHERE email = 'customer@localserve.com'", one=True)
            uid = u['user_id']
            enrollment = query_db("SELECT * FROM enrollments WHERE course_id = ? AND user_id = ?", (cid, uid), one=True)
            self.assertIsNotNone(enrollment)
            eid = enrollment['enrollment_id']
            lessons = query_db("SELECT lesson_id FROM course_lessons WHERE course_id = ?", (cid,))

        # Complete each lesson
        for l in lessons:
            comp_res = self.client.post(f'/skillshare/learn/{eid}/lesson/{l["lesson_id"]}/complete', follow_redirects=True)
            self.assertEqual(comp_res.status_code, 200)

        # Check certificate generated
        with self.app.app_context():
            cert = query_db("SELECT * FROM skill_certificates WHERE enrollment_id = ?", (eid,), one=True)
            self.assertIsNotNone(cert)
            self.assertTrue(cert['certificate_number'].startswith('LS-PLU-'))

    def test_certificate_public_verification(self):
        """Verify public lookup and certificate rendering via certificate number and code."""
        # Check pre-seeded certificate
        verif_res = self.client.get('/skillshare/verify/ls2026ele777')
        self.assertEqual(verif_res.status_code, 200)
        self.assertIn(b'Venkata Rao', verif_res.data)
        self.assertIn(b'LS-ELE-2026-00128', verif_res.data)
        self.assertIn(b'Certificate of Practical Course Completion', verif_res.data)

        # Search route
        lookup_res = self.client.get('/skillshare/verify?cert_id=LS-ELE-2026-00128', follow_redirects=True)
        self.assertEqual(lookup_res.status_code, 200)
        self.assertIn(b'Officially Verified', lookup_res.data)

    def test_workshops_and_skill_exchange(self):
        """Verify community workshops reservation and peer-to-peer barter posting."""
        self.client.get('/quick-login/customer')

        # Workshop list
        ws_res = self.client.get('/skillshare/workshops')
        self.assertEqual(ws_res.status_code, 200)
        self.assertIn(b'In-Person Community Workshops', ws_res.data)

        # Register for workshop
        with self.app.app_context():
            ws = query_db("SELECT session_id FROM training_sessions LIMIT 1", one=True)
            sid = ws['session_id']

        reg_res = self.client.post(f'/skillshare/session/{sid}/register', follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)

        # Post Skill Exchange
        post_res = self.client.post('/skillshare/exchange/post', data={
            'teach_skill': 'Two-Wheeler Carburetor Cleaning',
            'learn_skill': 'Pesticide Spray Machine Maintenance',
            'notes': 'Available on weekends.'
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)

        with self.app.app_context():
            ex = query_db("SELECT * FROM skill_exchanges WHERE teach_skill = 'Two-Wheeler Carburetor Cleaning'", one=True)
            self.assertIsNotNone(ex)

    def test_emergency_mode_and_assistant(self):
        """Verify Emergency Mode and Smart Assistant NLP intent parser."""
        # Emergency Mode view
        em_res = self.client.get('/emergency?problem=electrical')
        self.assertEqual(em_res.status_code, 200)
        self.assertIn(b'Community Emergency Mode', em_res.data)
        self.assertIn(b'Available', em_res.data)

        # Smart Assistant API: Tap leak
        asst_plumb = self.client.post('/api/assistant', json={'query': 'My tap is leaking water badly'})
        self.assertEqual(asst_plumb.status_code, 200)
        data1 = json.loads(asst_plumb.data)
        self.assertEqual(data1['intent'], 'service')
        self.assertEqual(data1['category'], 'Plumber')

        # Smart Assistant API: Fan repair
        asst_elec = self.client.post('/api/assistant', json={'query': 'Ceiling fan capacitor burnt'})
        self.assertEqual(asst_elec.status_code, 200)
        data2 = json.loads(asst_elec.data)
        self.assertEqual(data2['intent'], 'service')
        self.assertEqual(data2['category'], 'Electrician')

        # Smart Assistant API: Fever medicine
        asst_med = self.client.post('/api/assistant', json={'query': 'Need paracetamol for fever'})
        self.assertEqual(asst_med.status_code, 200)
        data3 = json.loads(asst_med.data)
        self.assertEqual(data3['intent'], 'medicine')

        # Smart Assistant API: Telugu query
        asst_te = self.client.post('/api/assistant', json={'query': 'కరెంట్ పోయింది స్విచ్ బోర్డు కాలింది'})
        self.assertEqual(asst_te.status_code, 200)
        data4 = json.loads(asst_te.data)
        self.assertEqual(data4['intent'], 'service')
        self.assertEqual(data4['category'], 'Electrician')

    def test_notices_and_volunteers(self):
        """Verify Panchayat Notice Board and Volunteers directory."""
        notices_res = self.client.get('/notices')
        self.assertEqual(notices_res.status_code, 200)
        self.assertIn(b'Panchayat', notices_res.data)

        vols_res = self.client.get('/volunteers')
        self.assertEqual(vols_res.status_code, 200)
        self.assertIn(b'Community Volunteers', vols_res.data)

if __name__ == '__main__':
    unittest.main()

