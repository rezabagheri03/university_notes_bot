from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os
import jdatetime

db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from .models.database import Admin
    return Admin.query.get(int(user_id))

def persian_date_filter(date):
    """Convert gregorian date to Persian date string."""
    if not date:
        return ""
    persian_date = jdatetime.date.fromgregorian(date=date)
    return persian_date.strftime("%Y/%m/%d")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Add custom Jinja2 filters
    app.jinja_env.filters['persian_date'] = persian_date_filter
    
    # Configure login
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'لطفاً برای دسترسی به این صفحه وارد شوید.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from .admin.routes import admin_bp
    from .routes import main
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(main)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create uploads directory if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
    
    return app

# Create the application instance
app = create_app()