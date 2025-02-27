from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os
# import jdatetime
import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'admin.login'

@login_manager.user_loader
def load_user(user_id):
    from app.models import Admin
    return Admin.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    from app.models import Admin, Note, Major, Semester, Lesson, Teacher, Rating, Subscription, User
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp)
    
    from app.bot import bp as bot_bp
    app.register_blueprint(bot_bp)
    
    from app.routes import main as main_bp
    app.register_blueprint(main_bp)
    
    @app.template_filter('jalali_date')
    def jalali_date(value):
        if value is None:
            return ""
        return value.strftime('%Y/%m/%d')
    
    return app

app = create_app()