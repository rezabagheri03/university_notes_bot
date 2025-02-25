from app import app, db
from app.models.database import Admin, Major, Semester, Lesson, Teacher, Note, Rating, User, Subscription

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables with new schema
        db.create_all()
        print("Database recreated successfully with new schema!")

if __name__ == "__main__":
    init_db()