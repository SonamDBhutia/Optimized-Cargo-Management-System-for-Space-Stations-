from models import Item, Container, Zone
from octree import Octree
import numpy as np
from app import db, logger
from datetime import datetime

def find_optimal_placement(item, containers=None):
    """Find the optimal placement for an item across all containers."""
    if containers is None:
        containers = Container.query.all()
    
    best_placement = None
    best_score = float('-inf')
    
    for container in containers:
        # Check if the item can fit in this container at all
        if (item.width > container.width and item.depth > container.width) or \
           (item.width > container.depth and item.depth > container.depth) or \
           item.height > container.height:
            continue
        
        # Prioritize containers in the preferred zone
        zone_match_score = 50 if container.zone_id == item.preferred_zone_id else 0
        
        # Create an octree for the container
        octree = Octree(container)
        
        # Find empty space in this container
        position = octree.find_empty_space(item.width, item.depth, item.height)
        
        if position:
            x, y, z, rotated = position
            
            # Calculate a placement score (lower y is better - closer to the front)
            # Higher priority items should have lower y values
            placement_score = 100 - (y / container.depth * 100)
            
            # Combine scores
            total_score = zone_match_score + placement_score + item.priority / 10
            
            if total_score > best_score:
                best_score = total_score
                best_placement = {
                    'container_id': container.id,
                    'x': x,
                    'y': y,
                    'z': z,
                    'rotated': rotated,
                    'score': total_score
                }
    
    return best_placement

def find_optimal_placements_for_batch(items):
    """Find optimal placements for a batch of items."""
    # Sort items by priority (highest first)
    sorted_items = sorted(items, key=lambda x: x.priority, reverse=True)
    
    # Get all containers
    containers = Container.query.all()
    container_octrees = {container.id: Octree(container) for container in containers}
    
    placements = []
    
    for item in sorted_items:
        best_placement = find_optimal_placement(item, containers)
        
        if best_placement:
            placements.append({
                'item_id': item.id,
                'item_name': item.name,
                'container_id': best_placement['container_id'],
                'x': best_placement['x'],
                'y': best_placement['y'],
                'z': best_placement['z'],
                'rotated': best_placement['rotated'],
                'score': best_placement['score']
            })
            
            # Update the octree for this container to reflect the new item placement
            container = next(c for c in containers if c.id == best_placement['container_id'])
            octree = container_octrees[container.id]
            
            # Temporarily set the item's position to use in the octree
            item.container_id = container.id
            item.x_pos = best_placement['x']
            item.y_pos = best_placement['y']
            item.z_pos = best_placement['z']
            item.rotated = best_placement['rotated']
            
            # Update the octree
            octree.insert(item)
    
    return placements

def find_item_to_retrieve(item_name):
    """Find the best item to retrieve based on name, expiry, and accessibility."""
    # Find items with matching name
    items = Item.query.filter(
        Item.name.ilike(f"%{item_name}%"),
        Item.is_waste == False,
        Item.container_id != None
    ).all()
    
    if not items:
        return None, "No matching items found in any container"
    
    best_item = None
    best_score = float('-inf')
    retrieval_info = None
    
    for item in items:
        # Get container
        container = Container.query.get(item.container_id)
        if not container:
            continue
        
        # Create octree for container
        octree = Octree(container)
        
        # Calculate retrieval steps
        steps, blocking_items = octree.calculate_retrieval_steps(item)
        
        # Calculate expiry score (items closer to expiry get higher scores)
        expiry_score = 0
        if item.expiry_date:
            days_until_expiry = (item.expiry_date - datetime.now().date()).days
            if days_until_expiry <= 0:
                expiry_score = 100  # Already expired
            else:
                expiry_score = max(0, 100 - days_until_expiry)  # Higher score as expiry approaches
        
        # Calculate usage score (items with fewer uses left get higher scores)
        usage_score = 0
        if item.usage_limit is not None and item.uses_remaining is not None:
            usage_percentage = item.uses_remaining / item.usage_limit
            usage_score = 100 * (1 - usage_percentage)  # Higher score as uses decrease
        
        # Calculate accessibility score (fewer steps is better)
        accessibility_score = 100 / (steps + 1)  # Avoid division by zero
        
        # Combine scores - weight can be adjusted based on importance
        total_score = (
            item.priority * 0.4 +  # Higher priority items preferred
            expiry_score * 0.3 +   # Items closer to expiry preferred
            usage_score * 0.1 +    # Items with fewer uses left preferred
            accessibility_score * 0.2  # More accessible items preferred
        )
        
        if total_score > best_score:
            best_score = total_score
            best_item = item
            retrieval_info = {
                'steps': steps,
                'blocking_items': [item.to_dict() for item in blocking_items]
            }
    
    if best_item:
        return best_item, retrieval_info
    else:
        return None, "No suitable item found for retrieval"

def suggest_rearrangement(container_id, new_items):
    """Suggest rearrangement of items to accommodate new items."""
    container = Container.query.get(container_id)
    if not container:
        return None, "Container not found"
    
    # Get current items in the container
    current_items = Item.query.filter_by(container_id=container_id, is_waste=False).all()
    
    # Create an octree for the container's current state
    octree = Octree(container)
    
    # Calculate total volume of current items and new items
    current_volume = sum(item.width * item.depth * item.height for item in current_items)
    new_volume = sum(item.width * item.depth * item.height for item in new_items)
    
    # Calculate container volume
    container_volume = container.width * container.depth * container.height
    
    # Check if there's enough space theoretically
    if current_volume + new_volume > container_volume * 0.9:  # Allow 90% max fill
        # Not enough space, need to remove some items
        # Sort current items by priority (lowest first)
        sorted_items = sorted(current_items, key=lambda x: x.priority)
        
        # Calculate how much volume we need to free
        volume_to_free = current_volume + new_volume - container_volume * 0.9
        
        # Select items to move until we free enough space
        items_to_move = []
        freed_volume = 0
        
        for item in sorted_items:
            item_volume = item.width * item.depth * item.height
            items_to_move.append(item)
            freed_volume += item_volume
            
            if freed_volume >= volume_to_free:
                break
        
        # Find alternative containers for these items
        alternative_placements = []
        
        for item in items_to_move:
            # Find containers excluding the current one
            other_containers = Container.query.filter(Container.id != container_id).all()
            
            placement = find_optimal_placement(item, other_containers)
            if placement:
                alternative_placements.append({
                    'item_id': item.id,
                    'item_name': item.name,
                    'current_container': container_id,
                    'suggested_container': placement['container_id'],
                    'x': placement['x'],
                    'y': placement['y'],
                    'z': placement['z'],
                    'rotated': placement['rotated']
                })
        
        # Return the suggestion to move these items
        return {
            'items_to_move': [item.to_dict() for item in items_to_move],
            'alternative_placements': alternative_placements,
            'volume_needed': volume_to_free,
            'volume_freed': freed_volume
        }, None
    
    # If there's enough space, find optimal placements for new items
    placements = find_optimal_placements_for_batch(new_items)
    
    return {
        'items_to_move': [],
        'new_item_placements': placements,
        'space_available': True
    }, None

def optimize_waste_return(max_weight=None):
    """Optimize waste items for return shipment."""
    # Get all waste items
    waste_items = Item.query.filter_by(is_waste=True).all()
    
    if not waste_items:
        return None, "No waste items found"
    
    # If no max weight specified, assume we can return all waste
    if max_weight is None:
        return {
            'items': [item.to_dict() for item in waste_items],
            'total_weight': sum(item.mass for item in waste_items),
            'total_items': len(waste_items)
        }, None
    
    # Sort waste items by mass/volume ratio (density) to optimize for weight
    sorted_items = sorted(
        waste_items, 
        key=lambda x: x.mass / (x.width * x.depth * x.height),
        reverse=True  # Higher density first
    )
    
    selected_items = []
    total_weight = 0
    
    for item in sorted_items:
        if total_weight + item.mass <= max_weight:
            selected_items.append(item)
            total_weight += item.mass
    
    # If we couldn't select any items, recommend the lightest one
    if not selected_items and waste_items:
        lightest_item = min(waste_items, key=lambda x: x.mass)
        return {
            'items': [lightest_item.to_dict()],
            'total_weight': lightest_item.mass,
            'total_items': 1,
            'note': f"Only returning lightest item as max weight ({max_weight} kg) is too restrictive"
        }, None
    
    return {
        'items': [item.to_dict() for item in selected_items],
        'total_weight': total_weight,
        'total_items': len(selected_items)
    }, None
