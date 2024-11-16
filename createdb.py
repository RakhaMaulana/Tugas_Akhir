import sqlite3

def create_database():
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blinded_message TEXT,
            signed_blinded_message TEXT,
            signed_message TEXT,
            n TEXT,
            e TEXT,
            message_hash TEXT,
            concatenated_message TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            id_number INTEGER PRIMARY KEY,
            has_voted BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def insert_voter(id_number):
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('INSERT INTO voters (id_number, has_voted) VALUES (?, 0)', (id_number,))
    conn.commit()
    conn.close()

create_database()
