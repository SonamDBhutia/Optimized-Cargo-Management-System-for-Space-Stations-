import unittest
from app import app, db
from models import Zone, Container, Item
import os
import tempfile
import json


class SpaceStationTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Add test data
            zone = Zone(name="Test Zone", description="For testing")
            db.session.add(zone)
            db.session.commit()
            
            container = Container(
                id="testCont1",
                width=100,
                depth=100, 
                height=100,
                zone_id=zone.id
            )
            db.session.add(container)
            db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_index_route(self):
        """Test the index route returns 200"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_zones_api(self):
        """Test the zones API endpoint"""
        response = self.client.get('/api/zones')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('zones', data)
        self.assertEqual(len(data['zones']), 1)
        self.assertEqual(data['zones'][0]['name'], "Test Zone")

    def test_containers_api(self):
        """Test the containers API endpoint"""
        response = self.client.get('/api/containers')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('containers', data)
        self.assertEqual(len(data['containers']), 1)
        self.assertEqual(data['containers'][0]['id'], "testCont1")


if __name__ == '__main__':
    unittest.main()