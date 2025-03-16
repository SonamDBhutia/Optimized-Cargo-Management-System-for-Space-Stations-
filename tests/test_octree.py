import unittest
from octree import Octree, OctreeNode
from models import Container, Item


class OctreeTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.container = Container(
            id="testCont",
            width=100,
            depth=100,
            height=100,
            zone_id=1
        )
        self.octree = Octree(self.container)
        
        # Create test items
        self.item1 = Item(
            id="item1",
            name="Test Item 1",
            width=20,
            depth=20,
            height=20,
            mass=1.0,
            priority=1,
            container_id=self.container.id,
            x_pos=10,
            y_pos=10,
            z_pos=10,
            rotated=False
        )
        
        self.item2 = Item(
            id="item2",
            name="Test Item 2",
            width=30,
            depth=30,
            height=30,
            mass=2.0,
            priority=2,
            container_id=self.container.id,
            x_pos=50,
            y_pos=50,
            z_pos=50,
            rotated=False
        )

    def test_octree_insertion(self):
        """Test inserting items into the octree"""
        self.octree.insert(self.item1)
        self.octree.insert(self.item2)
        
        # Query a box that contains item1
        box_min = (0, 0, 0)
        box_max = (30, 30, 30)
        results = self.octree.query_box(box_min, box_max)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "item1")
        
        # Query a box that contains both items
        box_min = (0, 0, 0)
        box_max = (100, 100, 100)
        results = self.octree.query_box(box_min, box_max)
        
        self.assertEqual(len(results), 2)
        
        # Query a box that contains no items
        box_min = (80, 80, 80)
        box_max = (90, 90, 90)
        results = self.octree.query_box(box_min, box_max)
        
        self.assertEqual(len(results), 0)

    def test_empty_space_finding(self):
        """Test finding empty space in the container"""
        self.octree.insert(self.item1)
        self.octree.insert(self.item2)
        
        # Find space for a small item (should succeed)
        result = self.octree.find_empty_space(10, 10, 10)
        self.assertIsNotNone(result)
        
        # Create a large item to fill most of container
        large_item = Item(
            id="large",
            name="Large Item",
            width=80,
            depth=80,
            height=80,
            mass=10.0,
            priority=3,
            container_id=self.container.id,
            x_pos=10,
            y_pos=10,
            z_pos=10,
            rotated=False
        )
        self.octree.insert(large_item)
        
        # Try to find space for an item that won't fit
        result = self.octree.find_empty_space(30, 30, 30)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()