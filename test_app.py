"""
Automated Test & Verification Suite for Smart Public Transport System
Tests all endpoints, database operations, security policies, and calculation logic.
"""

import unittest
from app import app
from db import query_db, init_db

class SmartTransportTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        # Ensure fresh clean seed
        init_db()

    def test_01_index_page(self):
        """Test landing page renders with status 200 and key text."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Smart Public Transport', response.data)
        self.assertIn(b'Active Transit Routes', response.data)

    def test_02_journey_planner_page(self):
        """Test Journey Planner page renders."""
        response = self.client.get('/journey-planner')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Smart Journey Planner', response.data)

    def test_03_api_plan_journey(self):
        """Test Journey Planner API with valid stops."""
        response = self.client.post('/api/plan-journey', json={
            'origin_id': 1,
            'destination_id': 2
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(data['distance_km'], 0)
        self.assertEqual(len(data['options']), 6)
        self.assertIn('baseline_car', data)

    def test_04_transport_routes(self):
        """Test public transport routes explorer."""
        response = self.client.get('/transport-routes')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'METRO-BLUE', response.data)
        self.assertIn(b'BUS-522-EV', response.data)

    def test_05_api_route_details(self):
        """Test Route Details API."""
        response = self.client.get('/api/route/1/details')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['route']['id'], 1)
        self.assertGreater(len(data['stops']), 0)
        self.assertGreater(len(data['schedules']), 0)

    def test_06_clean_mobility_page(self):
        """Test Clean Mobility & EV page."""
        response = self.client.get('/clean-mobility')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Clean Mobility & EV Infrastructure', response.data)
        self.assertIn(b'Tata EZ Charge', response.data)

    def test_07_api_ev_stations(self):
        """Test EV Stations JSON API."""
        response = self.client.get('/api/ev-stations')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(len(data['stations']), 0)

    def test_08_carbon_calculator(self):
        """Test Carbon Calculator page."""
        response = self.client.get('/carbon-calculator')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Carbon Emission & Savings Calculator', response.data)

    def test_09_api_calculate_emissions(self):
        """Test Emission Calculation API."""
        response = self.client.post('/api/calculate-emissions', json={
            'distance_km': 15.0,
            'period': 'annual',
            'trips_per_day': 2
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(data['baseline_car_kg'], 0)
        self.assertEqual(len(data['breakdown']), 7)

    def test_10_feedback_submission(self):
        """Test feedback submission."""
        response = self.client.post('/feedback', data={
            'name': 'Test Commuter',
            'email': 'tester@example.com',
            'category': 'General Suggestion',
            'rating': '5',
            'comment': 'Fantastic smart transit app for college project demonstration!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thank you! Your feedback and ratings have been recorded.', response.data)

    def test_11_auth_flow(self):
        """Test user login and dashboard access."""
        # Non-logged in dashboard redirect
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)

        # Login as user
        res_login = self.client.post('/login', data={
            'email': 'rahul.sharma@example.com',
            'password': 'User@123'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Welcome, Rahul Sharma', res_login.data)

        # Access dashboard
        res_dash = self.client.get('/dashboard')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b'Commuter Dashboard', res_dash.data)

        # Log out
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)

    def test_12_admin_panel_and_crud(self):
        """Test admin login, authorization protection, and CRUD operations."""
        # Unauthorized access to admin panel
        res_unauth = self.client.get('/admin')
        self.assertEqual(res_unauth.status_code, 302)

        # Login as admin
        self.client.post('/login', data={
            'email': 'admin@smartmobility.com',
            'password': 'Admin@123'
        }, follow_redirects=True)

        res_admin = self.client.get('/admin')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'System Governance & Analytics', res_admin.data)

        # 1. Add Route
        res_add_route = self.client.post('/admin/routes/add', data={
            'route_number': 'TEST-BUS-999',
            'route_name': 'Test Route Alpha',
            'mode_type': 'bus',
            'origin': 'Stop Alpha',
            'destination': 'Stop Beta',
            'distance_km': 10.0,
            'estimated_time_min': 20,
            'standard_fare': 15.0,
            'frequency_min': 10,
            'status': 'On Time'
        }, follow_redirects=True)
        self.assertIn(b'TEST-BUS-999', res_add_route.data)

        # Retrieve new route id
        new_route = query_db("SELECT id FROM routes WHERE route_number = 'TEST-BUS-999'", one=True)
        self.assertIsNotNone(new_route)

        # 2. Edit Route
        res_edit_route = self.client.post(f'/admin/routes/edit/{new_route["id"]}', data={
            'route_name': 'Test Route Alpha Updated',
            'mode_type': 'electric_bus',
            'origin': 'Stop Alpha',
            'destination': 'Stop Beta',
            'distance_km': 12.0,
            'estimated_time_min': 22,
            'standard_fare': 18.0,
            'frequency_min': 8,
            'status': 'High Frequency',
            'is_active': '1'
        }, follow_redirects=True)
        self.assertEqual(res_edit_route.status_code, 200)

        # 3. Delete Route
        res_del_route = self.client.post(f'/admin/routes/delete/{new_route["id"]}', follow_redirects=True)
        self.assertEqual(res_del_route.status_code, 200)
        check_deleted = query_db("SELECT id FROM routes WHERE route_number = 'TEST-BUS-999'", one=True)
        self.assertIsNone(check_deleted)

if __name__ == '__main__':
    unittest.main()
