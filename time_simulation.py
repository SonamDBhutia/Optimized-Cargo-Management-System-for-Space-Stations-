from models import Item, UsageLog, Container
from app import db, logger
from datetime import datetime, date, timedelta
from waste_management import check_for_waste_items

def simulate_next_day(items_used=None):
    """Simulate the passing of one day."""
    try:
        return advance_time(1, items_used)
    except Exception as e:
        logger.error(f"Error simulating next day: {str(e)}")
        return False, str(e)

def advance_time(days, items_used=None):
    """Advance the simulation by specified number of days."""
    try:
        if items_used is None:
            items_used = []
        
        # Process used items
        for item_usage in items_used:
            item_id = item_usage.get('id')
            uses = item_usage.get('uses', 1)
            
            item = Item.query.get(item_id)
            if not item:
                continue
                
            # Use the item the specified number of times
            for _ in range(uses):
                if item.use_item():
                    # Log the usage
                    log = UsageLog(
                        item_id=item.id,
                        action='used',
                        timestamp=datetime.utcnow(),
                        notes=f"Item used during time simulation"
                    )
                    db.session.add(log)
                else:
                    break  # Stop if item can't be used anymore
        
        # Check for items that have expired
        today = datetime.now().date()
        future_date = today + timedelta(days=days)
        
        # Find items that will expire in this period
        expiring_items = Item.query.filter(
            Item.expiry_date.isnot(None),
            Item.expiry_date <= future_date,
            Item.expiry_date > today,
            Item.is_waste == False
        ).all()
        
        # Mark expiring items as waste
        for item in expiring_items:
            item.is_waste = True
            
            # Log the expiration
            log = UsageLog(
                item_id=item.id,
                action='waste',
                timestamp=datetime.utcnow(),
                notes=f"Item expired on {item.expiry_date} during time simulation"
            )
            db.session.add(log)
        
        db.session.commit()
        
        # Check for any other waste items (e.g., used up during simulation)
        newly_wasted, _ = check_for_waste_items()
        
        # Return information about the simulation
        return {
            'days_advanced': days,
            'current_date': today.isoformat(),
            'new_date': future_date.isoformat(),
            'items_used': len(items_used),
            'items_expired': len(expiring_items),
            'other_waste_items': len(newly_wasted) if newly_wasted else 0
        }, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error advancing time: {str(e)}")
        return None, str(e)

def forecast_expirations(days=30):
    """Forecast items that will expire within the specified number of days."""
    try:
        today = datetime.now().date()
        forecast_date = today + timedelta(days=days)
        
        # Find items that will expire in this period
        expiring_items = Item.query.filter(
            Item.expiry_date.isnot(None),
            Item.expiry_date <= forecast_date,
            Item.expiry_date > today,
            Item.is_waste == False
        ).all()
        
        # Group items by expiry date
        expiry_forecast = {}
        
        for item in expiring_items:
            expiry_date = item.expiry_date.isoformat()
            
            if expiry_date not in expiry_forecast:
                expiry_forecast[expiry_date] = []
                
            expiry_forecast[expiry_date].append(item.to_dict())
        
        # Convert to list format for easier consumption by frontend
        forecast_list = [
            {
                'date': date,
                'days_from_now': (datetime.fromisoformat(date).date() - today).days,
                'items': items
            }
            for date, items in expiry_forecast.items()
        ]
        
        # Sort by date
        forecast_list.sort(key=lambda x: x['date'])
        
        return {
            'forecast_days': days,
            'expiring_items_count': len(expiring_items),
            'forecast': forecast_list
        }, None
    except Exception as e:
        logger.error(f"Error forecasting expirations: {str(e)}")
        return None, str(e)

def forecast_usage_depletion(days=30):
    """Forecast items that will be depleted based on usage patterns."""
    try:
        # For a simple implementation, we assume each consumable item
        # is used once every 7 days on average
        average_uses_per_week = 1
        
        # Calculate uses over the forecast period
        forecast_weeks = days / 7
        forecast_uses = forecast_weeks * average_uses_per_week
        
        # Find items that will be depleted in this period
        potentially_depleted = Item.query.filter(
            Item.uses_remaining.isnot(None),
            Item.uses_remaining <= forecast_uses,
            Item.is_waste == False
        ).all()
        
        # Group items by estimated depletion date
        depletion_forecast = {}
        
        for item in potentially_depleted:
            if item.uses_remaining is None or item.uses_remaining <= 0:
                continue
                
            # Estimate days until depletion
            days_until_depletion = int((item.uses_remaining / average_uses_per_week) * 7)
            depletion_date = (datetime.now().date() + timedelta(days=days_until_depletion)).isoformat()
            
            if depletion_date not in depletion_forecast:
                depletion_forecast[depletion_date] = []
                
            depletion_forecast[depletion_date].append(item.to_dict())
        
        # Convert to list format
        forecast_list = [
            {
                'date': date,
                'days_from_now': (datetime.fromisoformat(date).date() - datetime.now().date()).days,
                'items': items
            }
            for date, items in depletion_forecast.items()
        ]
        
        # Sort by date
        forecast_list.sort(key=lambda x: x['date'])
        
        return {
            'forecast_days': days,
            'depleting_items_count': len(potentially_depleted),
            'forecast': forecast_list
        }, None
    except Exception as e:
        logger.error(f"Error forecasting usage depletion: {str(e)}")
        return None, str(e)
