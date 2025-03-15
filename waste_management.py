from models import Item, UsageLog, Container
from app import db, logger
from datetime import datetime
import numpy as np
from octree import Octree
from algorithms import optimize_waste_return

def check_for_waste_items():
    """Check all items for waste status and update the database."""
    try:
        # Get all non-waste items
        items = Item.query.filter_by(is_waste=False).all()
        
        newly_wasted = []
        
        for item in items:
            if item.should_be_waste():
                item.is_waste = True
                
                # Log the change
                log = UsageLog(
                    item_id=item.id,
                    action='waste',
                    timestamp=datetime.utcnow(),
                    notes=f"Item automatically marked as waste: {'Expired' if item.is_expired() else 'Used up'}"
                )
                db.session.add(log)
                
                newly_wasted.append(item)
        
        db.session.commit()
        return newly_wasted, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error checking for waste items: {str(e)}")
        return None, str(e)

def prepare_waste_for_return(max_weight=None):
    """Prepare waste items for return shipment."""
    try:
        result, error = optimize_waste_return(max_weight)
        if error:
            return None, error
            
        return result, None
    except Exception as e:
        logger.error(f"Error preparing waste for return: {str(e)}")
        return None, str(e)

def move_waste_to_container(waste_item_id, container_id):
    """Move a waste item to a specific container for return."""
    try:
        item = Item.query.get(waste_item_id)
        if not item:
            return None, f"Item with ID {waste_item_id} not found"
        
        if not item.is_waste:
            return None, f"Item with ID {waste_item_id} is not marked as waste"
            
        container = Container.query.get(container_id)
        if not container:
            return None, f"Container with ID {container_id} not found"
        
        # Create octree for the container
        octree = Octree(container)
        
        # Find empty space in the container
        position = octree.find_empty_space(item.width, item.depth, item.height)
        
        if not position:
            return None, f"No suitable space found in container {container_id}"
            
        x, y, z, rotated = position
        
        # Record previous container for logging
        previous_container_id = item.container_id
        
        # Update item position
        item.container_id = container_id
        item.x_pos = x
        item.y_pos = y
        item.z_pos = z
        item.rotated = rotated
        
        db.session.commit()
        
        # Log the movement
        log = UsageLog(
            item_id=item.id,
            action='moved',
            timestamp=datetime.utcnow(),
            from_container_id=previous_container_id,
            to_container_id=container_id,
            notes=f"Waste item moved to container {container_id} for return"
        )
        db.session.add(log)
        db.session.commit()
        
        return item, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error moving waste to container: {str(e)}")
        return None, str(e)

def process_undock_event(container_id):
    """Process an undocking event for a container with waste."""
    try:
        container = Container.query.get(container_id)
        if not container:
            return None, f"Container with ID {container_id} not found"
        
        # Get all waste items in this container
        waste_items = Item.query.filter_by(container_id=container_id, is_waste=True).all()
        
        if not waste_items:
            return None, f"No waste items found in container {container_id}"
        
        # Document the waste items being returned
        waste_manifest = {
            'container_id': container_id,
            'undock_time': datetime.utcnow().isoformat(),
            'items': [item.to_dict() for item in waste_items],
            'total_items': len(waste_items),
            'total_mass': sum(item.mass for item in waste_items)
        }
        
        # Log the undocking for each item
        for item in waste_items:
            # Log the return
            log = UsageLog(
                item_id=item.id,
                action='returned',
                timestamp=datetime.utcnow(),
                from_container_id=container_id,
                notes=f"Waste item returned via container {container_id} undocking"
            )
            db.session.add(log)
            
            # Remove the item from the database or mark as returned
            # For this implementation, we'll keep the records but remove from container
            item.container_id = None
            item.x_pos = None
            item.y_pos = None
            item.z_pos = None
        
        db.session.commit()
        
        return waste_manifest, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing undock event: {str(e)}")
        return None, str(e)
