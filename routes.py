from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import Item, Container, Zone, UsageLog
import json

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Render the dashboard with overview statistics."""
    # Get summary statistics
    total_items = Item.query.count()
    total_waste = Item.query.filter_by(is_waste=True).count()
    total_containers = Container.query.count()
    
    # Recent logs
    recent_logs = UsageLog.query.order_by(UsageLog.timestamp.desc()).limit(10).all()
    
    # Total items by zone
    zones = Zone.query.all()
    zone_stats = []
    
    for zone in zones:
        containers = Container.query.filter_by(zone_id=zone.id).all()
        container_ids = [container.id for container in containers]
        
        items_count = Item.query.filter(
            Item.container_id.in_(container_ids),
            Item.is_waste == False
        ).count()
        
        zone_stats.append({
            'zone_name': zone.name,
            'items_count': items_count,
            'containers_count': len(containers)
        })
    
    return render_template(
        'dashboard.html',
        total_items=total_items,
        total_waste=total_waste,
        total_containers=total_containers,
        recent_logs=recent_logs,
        zone_stats=zone_stats
    )

@app.route('/items')
def items_page():
    """Render the items management page."""
    # Get all zones for the filters
    zones = Zone.query.all()
    
    return render_template('items.html', zones=zones)

@app.route('/containers')
def containers_page():
    """Render the containers management page."""
    # Get all zones
    zones = Zone.query.all()
    
    return render_template('containers.html', zones=zones)

@app.route('/simulation')
def simulation_page():
    """Render the time simulation page."""
    return render_template('simulation.html')

@app.route('/waste')
def waste_page():
    """Render the waste management page."""
    return render_template('waste.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
