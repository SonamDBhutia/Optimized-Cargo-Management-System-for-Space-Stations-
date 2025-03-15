from app import db
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship

class Zone(db.Model):
    """Represents a zone or area in the space station."""
    __tablename__ = 'zones'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    
    # Relationships
    containers = relationship("Container", back_populates="zone")
    
    def __repr__(self):
        return f"<Zone {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Container(db.Model):
    """Represents a storage container in the space station."""
    __tablename__ = 'containers'
    
    id = Column(String(50), primary_key=True)  # Container ID (e.g., contA)
    width = Column(Float, nullable=False)  # Width in cm
    depth = Column(Float, nullable=False)  # Depth in cm
    height = Column(Float, nullable=False)  # Height in cm
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    
    # Relationships
    zone = relationship("Zone", back_populates="containers")
    items = relationship("Item", back_populates="container")
    
    def __repr__(self):
        return f"<Container {self.id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'width': self.width,
            'depth': self.depth,
            'height': self.height,
            'zone_id': self.zone_id,
            'zone_name': self.zone.name if self.zone else None
        }

class Item(db.Model):
    """Represents an item stored in a container."""
    __tablename__ = 'items'
    
    id = Column(String(50), primary_key=True)  # Item ID (e.g., 001)
    name = Column(String(100), nullable=False)
    width = Column(Float, nullable=False)  # Width in cm
    depth = Column(Float, nullable=False)  # Depth in cm
    height = Column(Float, nullable=False)  # Height in cm
    mass = Column(Float, nullable=False)  # Mass in kg
    priority = Column(Integer, nullable=False)  # Priority (1-100)
    expiry_date = Column(Date, nullable=True)  # Can be null for non-expiring items
    usage_limit = Column(Integer, nullable=True)  # Can be null for non-consumable items
    uses_remaining = Column(Integer, nullable=True)  # Current uses remaining
    preferred_zone_id = Column(Integer, ForeignKey('zones.id'), nullable=True)
    container_id = Column(String(50), ForeignKey('containers.id'), nullable=True)
    
    # Position within container
    x_pos = Column(Float, nullable=True)  # Width position
    y_pos = Column(Float, nullable=True)  # Depth position
    z_pos = Column(Float, nullable=True)  # Height position
    
    # Item rotation (is the item rotated from its original orientation?)
    rotated = Column(Boolean, default=False)
    
    # Is this item waste?
    is_waste = Column(Boolean, default=False)
    
    # Relationships
    container = relationship("Container", back_populates="items")
    preferred_zone = relationship("Zone")
    usage_logs = relationship("UsageLog", back_populates="item")
    
    def __repr__(self):
        return f"<Item {self.id}: {self.name}>"
    
    def is_expired(self):
        """Check if the item is expired."""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date
    
    def is_used_up(self):
        """Check if the item has been fully used."""
        if self.uses_remaining is None:
            return False
        return self.uses_remaining <= 0
    
    def should_be_waste(self):
        """Check if the item should be marked as waste."""
        return self.is_expired() or self.is_used_up()
    
    def use_item(self):
        """Use the item once, reducing uses_remaining."""
        if self.uses_remaining is not None and self.uses_remaining > 0:
            self.uses_remaining -= 1
            # Check if item should now be waste
            if self.uses_remaining <= 0:
                self.is_waste = True
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'width': self.width,
            'depth': self.depth,
            'height': self.height,
            'mass': self.mass,
            'priority': self.priority,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'usage_limit': self.usage_limit,
            'uses_remaining': self.uses_remaining,
            'preferred_zone_id': self.preferred_zone_id,
            'preferred_zone_name': self.preferred_zone.name if self.preferred_zone else None,
            'container_id': self.container_id,
            'x_pos': self.x_pos,
            'y_pos': self.y_pos,
            'z_pos': self.z_pos,
            'rotated': self.rotated,
            'is_waste': self.is_waste,
            'is_expired': self.is_expired(),
            'is_used_up': self.is_used_up()
        }

class UsageLog(db.Model):
    """Logs when items are used or moved."""
    __tablename__ = 'usage_logs'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(String(50), ForeignKey('items.id'), nullable=False)
    action = Column(String(50), nullable=False)  # 'placed', 'retrieved', 'used', 'moved', 'waste'
    timestamp = Column(DateTime, default=datetime.utcnow)
    from_container_id = Column(String(50), nullable=True)
    to_container_id = Column(String(50), nullable=True)
    astronaut_name = Column(String(100), nullable=True)  # Who performed the action
    notes = Column(String(255), nullable=True)
    
    # Relationships
    item = relationship("Item", back_populates="usage_logs")
    
    def __repr__(self):
        return f"<UsageLog {self.id}: {self.action} on {self.item_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_name': self.item.name if self.item else None,
            'action': self.action,
            'timestamp': self.timestamp.isoformat(),
            'from_container_id': self.from_container_id,
            'to_container_id': self.to_container_id,
            'astronaut_name': self.astronaut_name,
            'notes': self.notes
        }
