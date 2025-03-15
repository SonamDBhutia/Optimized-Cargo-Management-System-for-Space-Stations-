from flask import Blueprint, request, jsonify
from models import Item, Container, Zone, UsageLog
from app import db, logger
from database import add_item, place_item, retrieve_item, get_retrieval_steps, advance_time, get_waste_items, mark_item_as_waste
from algorithms import find_optimal_placement, find_optimal_placements_for_batch, find_item_to_retrieve, suggest_rearrangement, optimize_waste_return
from waste_management import check_for_waste_items, prepare_waste_for_return, move_waste_to_container, process_undock_event
from time_simulation import simulate_next_day, advance_time, forecast_expirations, forecast_usage_depletion
import json
from datetime import datetime

api_bp = Blueprint('api', __name__)

# Helper function for API responses
def api_response(data=None, error=None, status=200):
    """Standard API response format."""
    response = {
        'success': error is None,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
        
    if error is not None:
        response['error'] = str(error)
        
    return jsonify(response), status

# Items API
@api_bp.route('/items', methods=['GET'])
def get_items():
    """Get all items."""
    try:
        # Optional filter by waste status
        waste_filter = request.args.get('waste', None)
        is_waste = None
        if waste_filter is not None:
            is_waste = waste_filter.lower() == 'true'
            
        query = Item.query
        if is_waste is not None:
            query = query.filter_by(is_waste=is_waste)
            
        items = query.all()
        return api_response([item.to_dict() for item in items])
    except Exception as e:
        logger.error(f"Error getting items: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/items/<string:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a specific item by ID."""
    try:
        item = Item.query.get(item_id)
        if not item:
            return api_response(error=f"Item with ID {item_id} not found", status=404)
            
        return api_response(item.to_dict())
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/items', methods=['POST'])
def create_item():
    """Create a new item."""
    try:
        data = request.json
        item, error = add_item(data)
        
        if error:
            return api_response(error=error, status=400)
            
        return api_response(item.to_dict(), status=201)
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/items/batch', methods=['POST'])
def create_items_batch():
    """Create multiple items at once."""
    try:
        data = request.json
        if not isinstance(data, list):
            return api_response(error="Expected a list of items", status=400)
            
        results = []
        for item_data in data:
            item, error = add_item(item_data)
            results.append({
                'id': item_data.get('id'),
                'success': error is None,
                'error': error
            })
            
        return api_response(results, status=201)
    except Exception as e:
        logger.error(f"Error creating items batch: {str(e)}")
        return api_response(error=str(e), status=500)

# Containers API
@api_bp.route('/containers', methods=['GET'])
def get_containers():
    """Get all containers."""
    try:
        containers = Container.query.all()
        return api_response([container.to_dict() for container in containers])
    except Exception as e:
        logger.error(f"Error getting containers: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/containers/<string:container_id>', methods=['GET'])
def get_container(container_id):
    """Get a specific container by ID."""
    try:
        container = Container.query.get(container_id)
        if not container:
            return api_response(error=f"Container with ID {container_id} not found", status=404)
            
        # Include items in this container
        container_data = container.to_dict()
        container_data['items'] = [item.to_dict() for item in Item.query.filter_by(container_id=container_id).all()]
        
        return api_response(container_data)
    except Exception as e:
        logger.error(f"Error getting container {container_id}: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/containers/<string:container_id>/contents', methods=['GET'])
def get_container_contents(container_id):
    """Get all items in a specific container."""
    try:
        container = Container.query.get(container_id)
        if not container:
            return api_response(error=f"Container with ID {container_id} not found", status=404)
            
        items = Item.query.filter_by(container_id=container_id).all()
        return api_response([item.to_dict() for item in items])
    except Exception as e:
        logger.error(f"Error getting container contents: {str(e)}")
        return api_response(error=str(e), status=500)

# Zones API
@api_bp.route('/zones', methods=['GET'])
def get_zones():
    """Get all zones."""
    try:
        zones = Zone.query.all()
        return api_response([zone.to_dict() for zone in zones])
    except Exception as e:
        logger.error(f"Error getting zones: {str(e)}")
        return api_response(error=str(e), status=500)

# Placement API
@api_bp.route('/placement/suggest', methods=['POST'])
def suggest_placement():
    """Suggest optimal placement for an item."""
    try:
        data = request.json
        item_id = data.get('item_id')
        
        item = Item.query.get(item_id)
        if not item:
            return api_response(error=f"Item with ID {item_id} not found", status=404)
            
        placement = find_optimal_placement(item)
        if not placement:
            return api_response(error="No suitable placement found", status=404)
            
        return api_response(placement)
    except Exception as e:
        logger.error(f"Error suggesting placement: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/placement/batch', methods=['POST'])
def suggest_batch_placement():
    """Suggest optimal placements for multiple items."""
    try:
        data = request.json
        item_ids = data.get('item_ids', [])
        
        if not item_ids:
            return api_response(error="No item IDs provided", status=400)
            
        items = Item.query.filter(Item.id.in_(item_ids)).all()
        if not items:
            return api_response(error="No valid items found", status=404)
            
        placements = find_optimal_placements_for_batch(items)
        return api_response(placements)
    except Exception as e:
        logger.error(f"Error suggesting batch placement: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/placement/execute', methods=['POST'])
def execute_placement():
    """Execute a placement of an item in a container."""
    try:
        data = request.json
        item_id = data.get('item_id')
        container_id = data.get('container_id')
        x = data.get('x')
        y = data.get('y')
        z = data.get('z')
        rotated = data.get('rotated', False)
        astronaut_name = data.get('astronaut_name')
        
        # Validate required fields
        if not all([item_id, container_id, x is not None, y is not None, z is not None]):
            return api_response(error="Missing required fields", status=400)
        
        item, error = place_item(item_id, container_id, x, y, z, rotated, astronaut_name)
        
        if error:
            return api_response(error=error, status=400)
            
        return api_response(item.to_dict())
    except Exception as e:
        logger.error(f"Error executing placement: {str(e)}")
        return api_response(error=str(e), status=500)

# Retrieval API
@api_bp.route('/retrieval/suggest', methods=['POST'])
def suggest_retrieval():
    """Suggest an item to retrieve based on name and other factors."""
    try:
        data = request.json
        item_name = data.get('item_name')
        
        if not item_name:
            return api_response(error="Item name is required", status=400)
            
        item, retrieval_info = find_item_to_retrieve(item_name)
        
        if not item:
            return api_response(error=f"No suitable item found for '{item_name}'", status=404)
            
        response_data = {
            'item': item.to_dict(),
            'retrieval_info': retrieval_info
        }
        
        return api_response(response_data)
    except Exception as e:
        logger.error(f"Error suggesting retrieval: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/retrieval/steps', methods=['GET'])
def get_item_retrieval_steps():
    """Get steps needed to retrieve a specific item."""
    try:
        item_id = request.args.get('item_id')
        
        if not item_id:
            return api_response(error="Item ID is required", status=400)
            
        steps, blocking_items = get_retrieval_steps(item_id)
        
        if steps is None:
            return api_response(error=blocking_items, status=404)  # Error message is in blocking_items
            
        return api_response({
            'item_id': item_id,
            'steps': steps,
            'blocking_items': blocking_items
        })
    except Exception as e:
        logger.error(f"Error getting retrieval steps: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/retrieval/execute', methods=['POST'])
def execute_retrieval():
    """Execute retrieval of an item."""
    try:
        data = request.json
        item_id = data.get('item_id')
        astronaut_name = data.get('astronaut_name')
        use_item = data.get('use_item', False)
        
        if not item_id:
            return api_response(error="Item ID is required", status=400)
            
        item, error = retrieve_item(item_id, astronaut_name, use_item)
        
        if error:
            return api_response(error=error, status=400)
            
        return api_response(item.to_dict())
    except Exception as e:
        logger.error(f"Error executing retrieval: {str(e)}")
        return api_response(error=str(e), status=500)

# Rearrangement API
@api_bp.route('/rearrangement/suggest', methods=['POST'])
def suggest_container_rearrangement():
    """Suggest rearrangement to accommodate new items."""
    try:
        data = request.json
        container_id = data.get('container_id')
        new_item_ids = data.get('new_item_ids', [])
        
        if not container_id:
            return api_response(error="Container ID is required", status=400)
            
        if not new_item_ids:
            return api_response(error="At least one new item ID is required", status=400)
            
        new_items = Item.query.filter(Item.id.in_(new_item_ids)).all()
        
        if not new_items:
            return api_response(error="No valid new items found", status=404)
            
        suggestion, error = suggest_rearrangement(container_id, new_items)
        
        if error:
            return api_response(error=error, status=400)
            
        return api_response(suggestion)
    except Exception as e:
        logger.error(f"Error suggesting rearrangement: {str(e)}")
        return api_response(error=str(e), status=500)

# Waste Management API
@api_bp.route('/waste/check', methods=['GET'])
def check_waste():
    """Check for items that should be marked as waste."""
    try:
        newly_wasted, error = check_for_waste_items()
        
        if error:
            return api_response(error=error, status=500)
            
        return api_response({
            'newly_wasted_count': len(newly_wasted) if newly_wasted else 0,
            'newly_wasted_items': [item.to_dict() for item in newly_wasted] if newly_wasted else []
        })
    except Exception as e:
        logger.error(f"Error checking waste: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/waste/items', methods=['GET'])
def get_all_waste():
    """Get all waste items."""
    try:
        waste_items, error = get_waste_items()
        
        if error:
            return api_response(error=error, status=500)
            
        return api_response(waste_items)
    except Exception as e:
        logger.error(f"Error getting waste items: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/waste/mark', methods=['POST'])
def mark_waste():
    """Mark an item as waste."""
    try:
        data = request.json
        item_id = data.get('item_id')
        reason = data.get('reason')
        
        if not item_id:
            return api_response(error="Item ID is required", status=400)
            
        item, error = mark_item_as_waste(item_id, reason)
        
        if error:
            return api_response(error=error, status=400)
            
        return api_response(item.to_dict())
    except Exception as e:
        logger.error(f"Error marking waste: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/waste/prepare-return', methods=['POST'])
def prepare_return():
    """Prepare waste items for return shipment."""
    try:
        data = request.json
        max_weight = data.get('max_weight')
        
        result, error = prepare_waste_for_return(max_weight)
        
        if error:
            return api_response(error=error, status=400)
            
        return api_response(result)
    except Exception as e:
        logger.error(f"Error preparing waste return: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/waste/move-to-container', methods=['POST'])
def move_waste():
    """Move a waste item to a container for return."""
    try:
        data = request.json
        item_id = data.get('item_id')
        container_id = data.get('container_id')
        
        if not item_id or not container_id:
            return api_response(error="Item ID and container ID are required", status=400)
            
        item, error = move_waste_to_container(item_id, container_id)
        
        if error:
            return api_response(error=error, status=400)
            
        return api_response(item.to_dict())
    except Exception as e:
        logger.error(f"Error moving waste to container: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/waste/undock', methods=['POST'])
def undock_waste():
    """Process an undocking event for a container with waste."""
    try:
        data = request.json
        container_id = data.get('container_id')
        
        if not container_id:
            return api_response(error="Container ID is required", status=400)
            
        result, error = process_undock_event(container_id)
        
        if error:
            return api_response(error=error, status=400)
            
        return api_response(result)
    except Exception as e:
        logger.error(f"Error undocking waste: {str(e)}")
        return api_response(error=str(e), status=500)

# Time Simulation API
@api_bp.route('/time/next-day', methods=['POST'])
def next_day():
    """Simulate the passing of one day."""
    try:
        data = request.json
        items_used = data.get('items_used', [])
        
        result, error = simulate_next_day(items_used)
        
        if error:
            return api_response(error=error, status=500)
            
        return api_response(result)
    except Exception as e:
        logger.error(f"Error simulating next day: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/time/advance', methods=['POST'])
def advance():
    """Advance time by specified number of days."""
    try:
        data = request.json
        days = data.get('days', 1)
        items_used = data.get('items_used', [])
        
        if days < 1:
            return api_response(error="Days must be at least 1", status=400)
            
        result, error = advance_time(days, items_used)
        
        if error:
            return api_response(error=error, status=500)
            
        return api_response(result)
    except Exception as e:
        logger.error(f"Error advancing time: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/time/forecast/expiry', methods=['GET'])
def forecast_expiry():
    """Forecast items that will expire within a time period."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1:
            return api_response(error="Days must be at least 1", status=400)
            
        result, error = forecast_expirations(days)
        
        if error:
            return api_response(error=error, status=500)
            
        return api_response(result)
    except Exception as e:
        logger.error(f"Error forecasting expiry: {str(e)}")
        return api_response(error=str(e), status=500)

@api_bp.route('/time/forecast/usage', methods=['GET'])
def forecast_usage():
    """Forecast items that will be depleted based on usage."""
    try:
        days = request.args.get('days', 30, type=int)
        
        if days < 1:
            return api_response(error="Days must be at least 1", status=400)
            
        result, error = forecast_usage_depletion(days)
        
        if error:
            return api_response(error=error, status=500)
            
        return api_response(result)
    except Exception as e:
        logger.error(f"Error forecasting usage: {str(e)}")
        return api_response(error=str(e), status=500)

# Logs API
@api_bp.route('/logs', methods=['GET'])
def get_logs():
    """Get usage logs with optional filtering."""
    try:
        # Optional filters
        item_id = request.args.get('item_id')
        action = request.args.get('action')
        astronaut = request.args.get('astronaut')
        limit = request.args.get('limit', 100, type=int)
        
        query = UsageLog.query
        
        if item_id:
            query = query.filter_by(item_id=item_id)
            
        if action:
            query = query.filter_by(action=action)
            
        if astronaut:
            query = query.filter(UsageLog.astronaut_name.ilike(f"%{astronaut}%"))
            
        # Order by timestamp (newest first)
        query = query.order_by(UsageLog.timestamp.desc())
        
        # Apply limit
        if limit > 0:
            query = query.limit(limit)
            
        logs = query.all()
        
        return api_response([log.to_dict() for log in logs])
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return api_response(error=str(e), status=500)
