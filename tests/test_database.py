import unittest
from app import app, db
from models import Zone, Container, Item, UsageLog
from database import (
    add_item, place_item, retrieve_item, 
    is_position_valid, get_retrieval_steps
)
import datetime
from sqlalchemy.sql import func


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        
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
        
        self.zone_id = zone.id
        self.container_id = container.id

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_item(self):
        """Test adding an item to the database"""
        item_data = {
            "id": "test001",
            "name": "Test Item",
            "width": 20,
            "depth": 20,
            "height": 20,
            "mass": 1.5,
            "priority": 3,
            "expiry_date": datetime.date.today() + datetime.timedelta(days=30),
            "usage_limit": 10,
            "uses_remaining": 10,
            "preferred_zone_id": self.zone_id
        }
        
        result = add_item(item_data)
        self.assertTrue(result)
        
        # Verify item was added
        item = Item.query.get("test001")
        self.assertIsNotNone(item)
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.mass, 1.5)
        self.assertEqual(item.priority, 3)
        self.assertEqual(item.uses_remaining, 10)

    def test_place_item(self):
        """Test placing an item in a container"""
        # First add an item
        item_data = {
            "id": "test002",
            "name": "Test Item 2",
            "width": 20,
            "depth": 20,
            "height": 20,
            "mass": 1.5,
            "priority": 3
        }
        add_item(item_data)
        
        # Place the item
        result = place_item(
            item_id="test002",
            container_id=self.container_id,
            x=10,
            y=10,
            z=10,
            astronaut_name="Test Astronaut"
        )
        
        self.assertTrue(result)
        
        # Verify placement
        item = Item.query.get("test002")
        self.assertEqual(item.container_id, self.container_id)
        self.assertEqual(item.x_pos, 10)
        self.assertEqual(item.y_pos, 10)
        self.assertEqual(item.z_pos, 10)
        
        # Check if log was created
        log = UsageLog.query.filter_by(item_id="test002").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, "placed")
        self.assertEqual(log.to_container_id, self.container_id)
        self.assertEqual(log.astronaut_name, "Test Astronaut")

    def test_is_position_valid(self):
        """Test position validation"""
        container = Container.query.get(self.container_id)
        
        # Add an item
        item_data = {
            "id": "test003",
            "name": "Test Item 3",
            "width": 20,
            "depth": 20,
            "height": 20,
            "mass": 1.5,
            "priority": 3
        }
        add_item(item_data)
        item = Item.query.get("test003")
        
        # Test valid position
        valid = is_position_valid(container, item, 10, 10, 10)
        self.assertTrue(valid)
        
        # Test invalid position (out of bounds)
        valid = is_position_valid(container, item, 90, 90, 90)
        self.assertFalse(valid)
        
        # Place an item and test collision
        place_item("test003", self.container_id, 10, 10, 10)
        
        # Add another item
        item_data = {
            "id": "test004",
            "name": "Test Item 4",
            "width": 20,
            "depth": 20,
            "height": 20,
            "mass": 1.5,
            "priority": 3
        }
        add_item(item_data)
        item2 = Item.query.get("test004")
        
        # Test collision detection
        valid = is_position_valid(container, item2, 20, 20, 20)
        self.assertFalse(valid)


if __name__ == '__main__':
    unittest.main()