from app import db, logger
from models import Zone, Container, Item, UsageLog
from datetime import datetime, date, timedelta

def initialize_db():
    """Initialize the database with starter data if needed."""
    # Check if zones exist
    if Zone.query.count() == 0:
        logger.info("Initializing database with starter zones...")
        # Create zones
        zones = [
            Zone(name="Crew Quarters", description="Living area for astronauts"),
            Zone(name="Airlock", description="Entry/exit point for spacewalks"),
            Zone(name="Laboratory", description="Scientific research area"),
            Zone(name="Medical Bay", description="Healthcare and medical treatment area"),
            Zone(name="Storage", description="General purpose storage area")
        ]
        db.session.add_all(zones)
        db.session.commit()
    
    # Check if containers exist
    if Container.query.count() == 0:
        logger.info("Initializing database with starter containers...")
        # Get zone IDs
        zones = {zone.name: zone.id for zone in Zone.query.all()}
        
        # Create containers
        containers = [
            Container(id="contA", width=100, depth=85, height=200, zone_id=zones["Crew Quarters"]),
            Container(id="contB", width=50, depth=85, height=200, zone_id=zones["Airlock"]),
            Container(id="contC", width=200, depth=85, height=200, zone_id=zones["Laboratory"]),
            Container(id="contD", width=150, depth=100, height=180, zone_id=zones["Medical Bay"]),
            Container(id="contE", width=200, depth=150, height=250, zone_id=zones["Storage"])
        ]
        db.session.add_all(containers)
        db.session.commit()

def add_item(item_data):
    """Add a new item to the database."""
    try:
        # Check if the item already exists
        existing_item = Item.query.get(item_data['id'])
        if existing_item:
            logger.warning(f"Item with ID {item_data['id']} already exists")
            return None, f"Item with ID {item_data['id']} already exists"
        
        # Lookup preferred zone ID if zone name provided
        if 'preferred_zone_name' in item_data and not 'preferred_zone_id' in item_data:
            zone = Zone.query.filter_by(name=item_data['preferred_zone_name']).first()
            if zone:
                item_data['preferred_zone_id'] = zone.id
            
        # Create new item
        item = Item(
            id=item_data['id'],
            name=item_data['name'],
            width=item_data['width'],
            depth=item_data['depth'],
            height=item_data['height'],
            mass=item_data['mass'],
            priority=item_data['priority'],
            usage_limit=item_data.get('usage_limit'),
            uses_remaining=item_data.get('usage_limit'),  # Initialize uses_remaining to usage_limit
            preferred_zone_id=item_data.get('preferred_zone_id'),
            is_waste=False
        )
        
        # Parse expiry date if provided
        if 'expiry_date' in item_data and item_data['expiry_date']:
            try:
                item.expiry_date = datetime.fromisoformat(item_data['expiry_date']).date()
            except ValueError:
                logger.warning(f"Invalid expiry date format: {item_data['expiry_date']}")
                # Set a default expiry date far in the future
                item.expiry_date = None
        
        db.session.add(item)
        db.session.commit()
        
        # Log the addition of the item
        log = UsageLog(
            item_id=item.id,
            action='added',
            timestamp=datetime.utcnow(),
            notes="Item added to inventory"
        )
        db.session.add(log)
        db.session.commit()
        
        return item, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding item: {str(e)}")
        return None, str(e)

def place_item(item_id, container_id, x, y, z, rotated=False, astronaut_name=None):
    """Place an item in a container at specified coordinates."""
    try:
        item = Item.query.get(item_id)
        if not item:
            return None, f"Item with ID {item_id} not found"
            
        container = Container.query.get(container_id)
        if not container:
            return None, f"Container with ID {container_id} not found"
        
        # Check if position is valid
        if not is_position_valid(container, item, x, y, z, rotated):
            return None, "Invalid position: item would not fit in container at this position"
        
        # Record previous container for logging
        previous_container_id = item.container_id
        
        # Update item position
        item.container_id = container_id
        item.x_pos = x
        item.y_pos = y
        item.z_pos = z
        item.rotated = rotated
        
        db.session.commit()
        
        # Log the placement
        log = UsageLog(
            item_id=item.id,
            action='placed' if previous_container_id is None else 'moved',
            timestamp=datetime.utcnow(),
            from_container_id=previous_container_id,
            to_container_id=container_id,
            astronaut_name=astronaut_name,
            notes=f"Item {'placed in' if previous_container_id is None else 'moved to'} container {container_id}"
        )
        db.session.add(log)
        db.session.commit()
        
        return item, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error placing item: {str(e)}")
        return None, str(e)

def is_position_valid(container, item, x, y, z, rotated=False):
    """Check if an item can be placed at the given position in the container."""
    # Get item dimensions based on rotation
    item_width = item.depth if rotated else item.width
    item_depth = item.width if rotated else item.depth
    item_height = item.height  # Height doesn't change with rotation
    
    # Check if item fits within container bounds
    if (x < 0 or y < 0 or z < 0 or 
        x + item_width > container.width or 
        y + item_depth > container.depth or 
        z + item_height > container.height):
        return False
    
    # Check if there's a collision with other items
    items_in_container = Item.query.filter_by(container_id=container.id).all()
    for other_item in items_in_container:
        if other_item.id == item.id:  # Skip the item itself if it's already in the container
            continue
            
        # Get other item dimensions based on rotation
        other_width = other_item.depth if other_item.rotated else other_item.width
        other_depth = other_item.width if other_item.rotated else other_item.depth
        other_height = other_item.height
        
        # Check for collision
        if not (x + item_width <= other_item.x_pos or 
                other_item.x_pos + other_width <= x or 
                y + item_depth <= other_item.y_pos or 
                other_item.y_pos + other_depth <= y or 
                z + item_height <= other_item.z_pos or 
                other_item.z_pos + other_height <= z):
            return False
    
    return True

def retrieve_item(item_id, astronaut_name=None, use_item=False):
    """Retrieve an item from its container."""
    try:
        item = Item.query.get(item_id)
        if not item:
            return None, f"Item with ID {item_id} not found"
        
        if not item.container_id:
            return None, f"Item with ID {item_id} is not in any container"
        
        # Record the container before removing
        container_id = item.container_id
        
        # Remove item from container
        item.container_id = None
        item.x_pos = None
        item.y_pos = None
        item.z_pos = None
        
        # Use the item if requested
        if use_item:
            item.use_item()  # This will decrement uses_remaining and potentially mark as waste
        
        db.session.commit()
        
        # Log the retrieval
        action = 'used' if use_item else 'retrieved'
        log = UsageLog(
            item_id=item.id,
            action=action,
            timestamp=datetime.utcnow(),
            from_container_id=container_id,
            astronaut_name=astronaut_name,
            notes=f"Item {action} from container {container_id}"
        )
        db.session.add(log)
        db.session.commit()
        
        return item, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error retrieving item: {str(e)}")
        return None, str(e)

def get_retrieval_steps(item_id):
    """Calculate steps needed to retrieve an item."""
    item = Item.query.get(item_id)
    if not item or not item.container_id:
        return None, "Item not found or not in a container"
    
    container = Container.query.get(item.container_id)
    if not container:
        return None, "Container not found"
    
    # Check if item is directly accessible from the open face
    if item.y_pos == 0:  # Item is at the front of container
        return 0, []
    
    # Find items that need to be moved to access this item
    blocking_items = Item.query.filter_by(container_id=container.id).all()
    items_to_move = []
    
    for other_item in blocking_items:
        if other_item.id == item.id:
            continue
        
        # Check if this item is blocking the path
        if (other_item.y_pos < item.y_pos and  # It's in front of our target item
            not (other_item.x_pos >= item.x_pos + item.width or  # Not to the right
                 other_item.x_pos + other_item.width <= item.x_pos or  # Not to the left
                 other_item.z_pos >= item.z_pos + item.height or  # Not above
                 other_item.z_pos + other_item.height <= item.z_pos)):  # Not below
            items_to_move.append(other_item.to_dict())
    
    return len(items_to_move), items_to_move

def advance_time(days=1, items_used=None):
    """Advance simulation time by specified number of days."""
    try:
        if items_used is None:
            items_used = []
        
        # Get current date
        current_date = date.today()
        
        # Calculate new date
        new_date = current_date + timedelta(days=days)
        
        # Update items that become waste due to expiry
        expired_items = Item.query.filter(
            Item.expiry_date.isnot(None),
            Item.expiry_date <= new_date,
            Item.is_waste == False
        ).all()
        
        for item in expired_items:
            item.is_waste = True
            log = UsageLog(
                item_id=item.id,
                action='waste',
                timestamp=datetime.utcnow(),
                notes=f"Item expired on {item.expiry_date}"
            )
            db.session.add(log)
        
        # Process used items
        for item_info in items_used:
            item_id = item_info.get('id')
            uses = item_info.get('uses', 1)
            
            item = Item.query.get(item_id)
            if not item:
                continue
                
            # Use the item the specified number of times
            for _ in range(uses):
                if item.use_item():
                    log = UsageLog(
                        item_id=item.id,
                        action='used',
                        timestamp=datetime.utcnow(),
                        notes=f"Item used during time simulation"
                    )
                    db.session.add(log)
                else:
                    break  # Stop if item can't be used anymore
        
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error advancing time: {str(e)}")
        return False, str(e)

def get_waste_items():
    """Get all items marked as waste."""
    try:
        waste_items = Item.query.filter_by(is_waste=True).all()
        return [item.to_dict() for item in waste_items], None
    except Exception as e:
        logger.error(f"Error getting waste items: {str(e)}")
        return None, str(e)

def mark_item_as_waste(item_id, reason=None):
    """Mark an item as waste."""
    try:
        item = Item.query.get(item_id)
        if not item:
            return None, f"Item with ID {item_id} not found"
        
        item.is_waste = True
        
        # Log the waste marking
        log = UsageLog(
            item_id=item.id,
            action='waste',
            timestamp=datetime.utcnow(),
            notes=reason or "Item manually marked as waste"
        )
        db.session.add(log)
        db.session.commit()
        
        return item, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking item as waste: {str(e)}")
        return None, str(e)
