import sqlite3

def initialize_databse():
    #Connect to databse 
    conn = sqlite3.connect('copilot.db')
    cursor = conn.cursor()

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS linksubmissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            url TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_databse()
    print("Databse initialized")
