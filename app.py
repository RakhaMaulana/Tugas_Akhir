from flask import Flask, request, render_template_string, redirect, url_for, flash, session
from main import poll_machine
from createdb import insert_voter
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages and session management
pm = poll_machine()

def get_admin_password_hash():
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('SELECT password_hash FROM admin LIMIT 1')
    password_hash = c.fetchone()[0]
    conn.close()
    return password_hash

@app.route('/')
def index():
    return render_template_string('''
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <title>Poll</title>
          </head>
          <body>
            <div class="container">
              <h1 class="mt-5">Poll</h1>
              <form action="/vote" method="post" class="mt-3">
                <div class="form-group">
                  <label for="poll_answer">Poll Answer</label>
                  <input type="text" class="form-control" id="poll_answer" name="poll_answer" required>
                </div>
                <div class="form-group">
                  <label for="id_number">ID Number</label>
                  <input type="number" class="form-control" id="id_number" name="id_number" required>
                </div>
                <button type="submit" class="btn btn-primary">Submit</button>
              </form>
            </div>
            <script>
              {% with messages = get_flashed_messages() %}
                {% if messages %}
                  {% for message in messages %}
                    alert("{{ message }}");
                  {% endfor %}
                {% endif %}
              {% endwith %}
            </script>
          </body>
        </html>
    ''')

@app.route('/vote', methods=['POST'])
def vote():
    poll_answer = request.form['poll_answer']
    id_number = int(request.form['id_number'])
    if not pm.p.is_valid_voter(id_number):
        flash("ID number tidak valid atau sudah digunakan untuk voting.")
        return redirect(url_for('index'))
    pm.start_poll(poll_answer, id_number)
    flash("Vote submitted! Check the CLI for details.")
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if 'admin_authenticated' in session and session['admin_authenticated']:
        return render_template_string('''
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
                <title>Admin</title>
              </head>
              <body>
                <div class="container">
                  <h1 class="mt-5">Admin</h1>
                  <form action="/register" method="post" class="mt-3">
                    <div class="form-group">
                      <label for="voter_id">Voter ID</label>
                      <input type="number" class="form-control" id="voter_id" name="voter_id" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Register Voter</button>
                  </form>
                  <form action="/logout" method="post" class="mt-3">
                    <button type="submit" class="btn btn-secondary">Logout</button>
                  </form>
                </div>
                <script>
                  {% with messages = get_flashed_messages() %}
                    {% if messages %}
                      {% for message in messages %}
                        alert("{{ message }}");
                      {% endfor %}
                    {% endif %}
                  {% endwith %}
                </script>
              </body>
            </html>
        ''')
    else:
        return render_template_string('''
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
                <title>Admin Login</title>
              </head>
              <body>
                <div class="container">
                  <h1 class="mt-5">Admin Login</h1>
                  <form action="/admin_login" method="post" class="mt-3">
                    <div class="form-group">
                      <label for="password">Admin Password</label>
                      <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Login</button>
                  </form>
                </div>
                <script>
                  {% with messages = get_flashed_messages() %}
                    {% if messages %}
                      {% for message in messages %}
                        alert("{{ message }}");
                      {% endfor %}
                    {% endif %}
                  {% endwith %}
                </script>
              </body>
            </html>
        ''')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form['password']
    password_hash = get_admin_password_hash()
    if bcrypt.checkpw(password.encode('utf-8'), password_hash):
        session['admin_authenticated'] = True
        flash("Admin authenticated successfully!")
        return redirect(url_for('admin'))
    else:
        flash("Unauthorized access!")
        return redirect(url_for('admin'))

@app.route('/register', methods=['POST'])
def register():
    if 'admin_authenticated' not in session or not session['admin_authenticated']:
        flash("Please login as admin first!")
        return redirect(url_for('admin'))

    voter_id = int(request.form['voter_id'])
    try:
        insert_voter(voter_id)
    except sqlite3.IntegrityError:
        flash("Voter already exists!")
        return redirect(url_for('admin'))
    flash("Voter registered successfully!")
    return redirect(url_for('admin'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_authenticated', None)
    flash("Logged out successfully!")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)