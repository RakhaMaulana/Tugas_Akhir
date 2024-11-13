import sqlite3

def create_database():
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS votes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  blinded_message TEXT,
                  signed_blinded_message TEXT,
                  signed_message TEXT,
                  n TEXT,
                  e TEXT,
                  message_hash TEXT,
                  concatenated_message TEXT)''')
    conn.commit()
    conn.close()

create_database()