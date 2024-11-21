import sqlite3
import bcrypt
from flask import Flask, request, redirect, url_for, flash, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_database():
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
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
            has_voted BOOLEAN NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            photo TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            number INTEGER NOT NULL,
            photo TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_voter(id_number):
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM voters WHERE id_number = ?', (id_number,))
    if c.fetchone()[0] > 0:
        conn.close()
        raise sqlite3.IntegrityError("Voter already exists")
    c.execute('INSERT INTO voters (id_number, has_voted) VALUES (?, 0)', (id_number,))
    conn.commit()
    conn.close()

def insert_admin_password(password):
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    c.execute('INSERT INTO admin (password_hash) VALUES (?)', (password_hash,))
    conn.commit()
    conn.close()

create_database()
# Insert the admin password (run this only once to set the password)
insert_admin_password('admin123')