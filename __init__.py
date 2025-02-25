from flask import Flask
from flask_login import LoginManager
from .models.database import db, Admin
from .admin.routes import admin_bp
from config import Config
import os

login_manager = LoginManager()

@login_manager.user_loader
def load_user(id):
    return Admin.query.get(int(id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    
    # Register blueprints
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app 