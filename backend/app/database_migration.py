import sqlite3
from datetime import datetime
from .database import DB_FILE

def migrate_database():
    """
    Migrate the database to add the status column to the items table.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if status column exists
    c.execute("PRAGMA table_info(items)")
    columns = c.fetchall()
    status_exists = any(column[1] == 'status' for column in columns)
    
    if not status_exists:
        try:
            # Add status column with default value 'Active'
            c.execute("ALTER TABLE items ADD COLUMN status TEXT DEFAULT 'Active'")
            
            # Update existing items that might be waste based on expiry date
            current_date = datetime.now().isoformat()
            c.execute("""
                UPDATE items 
                SET status = 'Waste' 
                WHERE (expiry_date IS NOT NULL AND expiry_date <= ?) 
                OR (usage_limit IS NOT NULL AND usage_limit <= 0)
            """, (current_date,))
            
            conn.commit()
            print("Database migration successful: Added status column to items table")
        except Exception as e:
            conn.rollback()
            print(f"Database migration failed: {str(e)}")
    else:
        print("Status column already exists in items table")
    
    conn.close()

if __name__ == "__main__":
    migrate_database()
