import sqlite3

def initialize_databse():
    #Connect to databse 
    conn = sqlite3.connect('copilot.db')
    cursor = conn.cursor()

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS linksubmissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL,
            canon_url TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending','queued','fetching','parsed','error')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                   
            price_monthly INTEGER,
            beds FLOAT,
            baths FLOAT,
            sqft INTEGER,
            address_full TEXT,
            photo_count INTEGER,
                   
            title TEXT,
            source_domain TEXT,
            source_provider TEXT,
            raw_payload TEXT,
                   
            parsed_at DATETIME,
            fetch_ms INTEGER,
            status_reason TEXT
        )
''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_databse()
    print("Databse initialized")
