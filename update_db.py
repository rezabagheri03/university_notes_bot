from app import create_app, db
from app.models.database import Note, Rating

def update_database():
    app = create_app()
    with app.app_context():
        # Add new columns
        try:
            db.session.execute('ALTER TABLE note ADD COLUMN rating_sum INTEGER DEFAULT 0')
            db.session.execute('ALTER TABLE note ADD COLUMN rating_count INTEGER DEFAULT 0')
            db.session.commit()
            print("Added new rating columns successfully!")
        except Exception as e:
            print(f"Error adding columns (they might already exist): {e}")
            db.session.rollback()
        
        # Update existing notes with ratings
        try:
            notes = Note.query.all()
            for note in notes:
                ratings = [r.value for r in note.ratings]
                note.rating_count = len(ratings)
                note.rating_sum = sum(ratings) if ratings else 0
            db.session.commit()
            print("Updated existing notes with rating data!")
        except Exception as e:
            print(f"Error updating notes: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_database() 