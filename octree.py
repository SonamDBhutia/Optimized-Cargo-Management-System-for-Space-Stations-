import numpy as np
from models import Item, Container

class OctreeNode:
    """Octree node for spatial partitioning."""
    
    def __init__(self, center, size, depth=0, max_depth=8, max_items=4):
        self.center = center  # (x, y, z) center of this node
        self.size = size      # size of this node's bounding box
        self.depth = depth    # current depth in the tree
        self.max_depth = max_depth  # maximum allowed depth
        self.max_items = max_items  # maximum items before subdivision
        
        self.items = []       # items contained in this node
        self.children = None  # child nodes (will be initialized if needed)
        
        # Calculate bounds
        half_size = size / 2
        self.bounds = {
            'min': np.array([center[0] - half_size, center[1] - half_size, center[2] - half_size]),
            'max': np.array([center[0] + half_size, center[1] + half_size, center[2] + half_size])
        }
    
    def subdivide(self):
        """Subdivide this node into 8 child nodes."""
        if self.children is not None:
            return  # Already subdivided
        
        half_size = self.size / 2
        quarter_size = half_size / 2
        
        # Create 8 children
        self.children = []
        for x in [-1, 1]:
            for y in [-1, 1]:
                for z in [-1, 1]:
                    center = np.array([
                        self.center[0] + x * quarter_size,
                        self.center[1] + y * quarter_size,
                        self.center[2] + z * quarter_size
                    ])
                    
                    child = OctreeNode(
                        center=center,
                        size=half_size,
                        depth=self.depth + 1,
                        max_depth=self.max_depth,
                        max_items=self.max_items
                    )
                    self.children.append(child)
        
        # Redistribute items to children
        items_to_redistribute = self.items
        self.items = []
        
        for item in items_to_redistribute:
            self.insert(item)
    
    def contains_point(self, point):
        """Check if a point is within this node's boundaries."""
        return (
            self.bounds['min'][0] <= point[0] <= self.bounds['max'][0] and
            self.bounds['min'][1] <= point[1] <= self.bounds['max'][1] and
            self.bounds['min'][2] <= point[2] <= self.bounds['max'][2]
        )
    
    def intersects_box(self, box_min, box_max):
        """Check if a box intersects with this node's boundaries."""
        return (
            self.bounds['min'][0] <= box_max[0] and
            self.bounds['max'][0] >= box_min[0] and
            self.bounds['min'][1] <= box_max[1] and
            self.bounds['max'][1] >= box_min[1] and
            self.bounds['min'][2] <= box_max[2] and
            self.bounds['max'][2] >= box_min[2]
        )
    
    def insert(self, item):
        """Insert an item into this node or its children."""
        # Calculate item bounds
        item_min = np.array([item.x_pos, item.y_pos, item.z_pos])
        item_width = item.depth if item.rotated else item.width
        item_depth = item.width if item.rotated else item.depth
        item_max = np.array([
            item.x_pos + item_width,
            item.y_pos + item_depth,
            item.z_pos + item.height
        ])
        
        # Check if item intersects with this node
        if not self.intersects_box(item_min, item_max):
            return False
        
        # If we have children, try to insert into them
        if self.children is not None:
            inserted = False
            for child in self.children:
                if child.insert(item):
                    inserted = True
            
            # If item doesn't fit completely in any child, keep it in this node
            if not inserted:
                self.items.append(item)
            
            return True
        
        # If no children and we're not at max depth and we have too many items, subdivide
        if len(self.items) >= self.max_items and self.depth < self.max_depth:
            self.subdivide()
            return self.insert(item)  # Try again with new children
        
        # Otherwise, keep the item in this node
        self.items.append(item)
        return True
    
    def query_box(self, box_min, box_max):
        """Query all items that intersect with the given box."""
        # If this node doesn't intersect with the query box, return empty list
        if not self.intersects_box(box_min, box_max):
            return []
        
        result = []
        
        # Check items in this node
        for item in self.items:
            item_min = np.array([item.x_pos, item.y_pos, item.z_pos])
            item_width = item.depth if item.rotated else item.width
            item_depth = item.width if item.rotated else item.depth
            item_max = np.array([
                item.x_pos + item_width,
                item.y_pos + item_depth,
                item.z_pos + item.height
            ])
            
            if (
                box_min[0] <= item_max[0] and box_max[0] >= item_min[0] and
                box_min[1] <= item_max[1] and box_max[1] >= item_min[1] and
                box_min[2] <= item_max[2] and box_max[2] >= item_min[2]
            ):
                result.append(item)
        
        # Query children if they exist
        if self.children is not None:
            for child in self.children:
                result.extend(child.query_box(box_min, box_max))
        
        return result

class Octree:
    """Octree implementation for efficient spatial queries on items in a container."""
    
    def __init__(self, container):
        """Initialize an octree for a container."""
        self.container = container
        
        # Create the root node centered in the container
        center = np.array([
            container.width / 2,
            container.depth / 2,
            container.height / 2
        ])
        
        # Size should be the maximum dimension to ensure the tree covers the entire container
        size = max(container.width, container.depth, container.height)
        
        self.root = OctreeNode(center, size)
        
        # Insert all items in the container
        self.rebuild()
    
    def rebuild(self):
        """Rebuild the octree with all items in the container."""
        # Clear the root and create a new one
        center = np.array([
            self.container.width / 2,
            self.container.depth / 2,
            self.container.height / 2
        ])
        size = max(self.container.width, self.container.depth, self.container.height)
        self.root = OctreeNode(center, size)
        
        # Insert all items
        items = Item.query.filter_by(container_id=self.container.id).all()
        for item in items:
            self.insert(item)
    
    def insert(self, item):
        """Insert an item into the octree."""
        return self.root.insert(item)
    
    def query_box(self, min_point, max_point):
        """Query all items that intersect with the given box."""
        return self.root.query_box(min_point, max_point)
    
    def find_empty_space(self, item_width, item_depth, item_height, consider_rotation=True):
        """Find empty space in the container that can fit an item of the given dimensions."""
        
        # We'll search in a grid pattern to find suitable spaces
        step_size = 5  # Step size in cm for the grid search
        
        best_position = None
        best_distance = float('inf')  # Distance from the open face (smaller is better)
        
        dimensions_to_try = [(item_width, item_depth, item_height)]
        if consider_rotation:
            dimensions_to_try.append((item_depth, item_width, item_height))
        
        for width, depth, height in dimensions_to_try:
            # Check grid positions
            for x in range(0, int(self.container.width - width) + 1, step_size):
                for y in range(0, int(self.container.depth - depth) + 1, step_size):
                    for z in range(0, int(self.container.height - height) + 1, step_size):
                        # Define the box for this position
                        box_min = np.array([x, y, z])
                        box_max = np.array([x + width, y + depth, z + height])
                        
                        # Query items that intersect with this box
                        intersecting_items = self.query_box(box_min, box_max)
                        
                        if not intersecting_items:
                            # This is an empty space
                            distance = y  # Distance from the open face of the container
                            
                            if distance < best_distance:
                                is_rotated = (width != item_width)  # Check if dimensions were rotated
                                best_position = (x, y, z, is_rotated)
                                best_distance = distance
        
        return best_position
    
    def get_items_blocking_path(self, item):
        """Get all items blocking the path to the open face for a given item."""
        if not item.container_id or item.container_id != self.container.id:
            return []
        
        # Calculate item bounds
        item_min = np.array([item.x_pos, item.y_pos, item.z_pos])
        item_width = item.depth if item.rotated else item.width
        item_depth = item.width if item.rotated else item.depth
        item_max = np.array([
            item.x_pos + item_width,
            item.y_pos + item_depth,
            item.z_pos + item.height
        ])
        
        # Define the path to the open face
        path_min = np.array([item_min[0], 0, item_min[2]])
        path_max = np.array([item_max[0], item_min[1], item_max[2]])
        
        # Query items intersecting with the path
        blocking_items = self.query_box(path_min, path_max)
        
        # Filter out the item itself
        blocking_items = [i for i in blocking_items if i.id != item.id]
        
        return blocking_items
    
    def calculate_retrieval_steps(self, item):
        """Calculate the number of steps needed to retrieve an item."""
        blocking_items = self.get_items_blocking_path(item)
        return len(blocking_items), blocking_items
