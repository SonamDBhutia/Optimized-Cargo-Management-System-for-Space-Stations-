import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "space-cargo-manager-secret")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///space_cargo.db"
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize db with app
db.init_app(app)

# Import routes after app is created to avoid circular imports
from api import api_bp
from database import initialize_db

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

# Create application context
with app.app_context():
    import models  # Import models to ensure they're registered
    db.create_all()  # Create database tables
    
    # Initialize the database with sample containers and zones if needed
    initialize_db()

# Import routes
import routes
