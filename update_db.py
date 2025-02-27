from app import create_app, db
from app.models.database import Note, Rating, User
from datetime import datetime
from sqlalchemy import text

def update_database():
    app = create_app()
    with app.app_context():
        # Drop and recreate all tables
        print("Recreating database tables...")
        db.drop_all()
        db.create_all()
        print("Database tables recreated successfully!")
        
        try:
            # Initialize any default data if needed
            print("Database update completed successfully!")
            
        except Exception as e:
            print(f"Error during database update: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_database() 