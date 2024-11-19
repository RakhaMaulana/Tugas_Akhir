from flask import Flask, request, render_template_string, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import os
import sqlite3
import bcrypt
from main import poll_machine  # Import poll_machine
from createdb import insert_voter  # Import insert_voter

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages and session management
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

pm = poll_machine()  # Initialize poll_machine

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_admin_password_hash():
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('SELECT password_hash FROM admin LIMIT 1')
    password_hash = c.fetchone()[0]
    conn.close()
    return password_hash

def get_candidates():
    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('SELECT id, name, class, number, photo FROM candidates')
    candidates = c.fetchall()
    conn.close()
    return candidates

@app.route('/')
def index():
    candidates = get_candidates()
    return render_template_string('''
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <title>Poll</title>
            <style>
              .candidate-photo {
                max-width: 300px;
                height: auto;
                margin-top: 20px;
              }
              .candidate-info {
                text-align: center;
                margin-top: 20px;
              }
              .form-section {
                margin-bottom: 30px;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <h1 class="mt-5 text-center">Dont be abstain. Your choice is important :D</h1>
              {% if candidates %}
              <form action="/vote" method="post" class="mt-3">
                <div class="form-section">
                  <label for="id_number" class="form-label">ID Number</label>
                  <input type="number" class="form-control" id="id_number" name="id_number" required>
                </div>
                <div class="candidate-info">
                  <img id="candidate-photo" class="candidate-photo" src="{{ url_for('uploaded_file', filename=candidates[0][4]) }}" alt="Candidate Photo">
                  <h5 id="candidate-name">{{ candidates[0][1] }}</h5>
                  <p id="candidate-class">{{ candidates[0][2] }}</p>
                </div>
                <div class="form-section">
                  <label for="poll_answer" class="form-label">Select Candidate</label>
                  <select class="form-control" id="poll_answer" name="poll_answer" required onchange="updateCandidateInfo()">
                    {% for candidate in candidates %}
                      <option value="{{ candidate[3] }}" data-photo="{{ url_for('uploaded_file', filename=candidate[4]) }}" data-name="{{ candidate[1] }}" data-class="{{ candidate[2] }}">{{ candidate[3] }}</option>
                    {% endfor %}
                  </select>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Submit</button>
              </form>
              {% else %}
              <p class="text-center">No candidates available.</p>
              {% endif %}
            </div>

            <!-- Modal -->
            <div class="modal fade" id="voteModal" tabindex="-1" aria-labelledby="voteModalLabel" aria-hidden="true">
              <div class="modal-dialog">
                <div class="modal-content">
                  <div class="modal-header">
                    <h5 class="modal-title" id="voteModalLabel">Vote Submitted</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                      <span aria-hidden="true">&times;</span>
                    </button>
                  </div>
                  <div class="modal-body">
                    Your vote has been submitted successfully!
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                  </div>
                </div>
              </div>
            </div>

            <script>
              function updateCandidateInfo() {
                var select = document.getElementById('poll_answer');
                var selectedOption = select.options[select.selectedIndex];
                var photo = selectedOption.getAttribute('data-photo');
                var name = selectedOption.getAttribute('data-name');
                var classInfo = selectedOption.getAttribute('data-class');

                document.getElementById('candidate-photo').src = photo;
                document.getElementById('candidate-name').innerText = name;
                document.getElementById('candidate-class').innerText = classInfo;
              }

              // Initialize candidate info with the first candidate's data
              if (document.getElementById('poll_answer').options.length > 0) {
                updateCandidateInfo();
              }

              // Show modal if vote was submitted
              {% with messages = get_flashed_messages() %}
                {% if messages %}
                  $('#voteModal').modal('show');
                {% endif %}
              {% endwith %}
            </script>
            <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
            <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
          </body>
        </html>
    ''', candidates=candidates)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/vote', methods=['POST'])
def vote():
    poll_answer = request.form['poll_answer']
    id_number = int(request.form['id_number'])
    if not pm.p.is_valid_voter(id_number):
        flash("ID number tidak valid atau sudah digunakan untuk voting.")
        return redirect(url_for('index'))
    pm.start_poll(poll_answer, id_number)
    flash("Vote submitted successfully!")
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
                  <form action="/register_voter" method="post" class="mt-3">
                    <div class="form-group">
                      <label for="voter_id">Voter ID</label>
                      <input type="number" class="form-control" id="voter_id" name="voter_id" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Register Voter</button>
                  </form>
                  <form action="/register_candidate" method="post" enctype="multipart/form-data" class="mt-3">
                    <div class="form-group">
                      <label for="name">Candidate Name</label>
                      <input type="text" class="form-control" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                      <label for="class">Class</label>
                      <input type="text" class="form-control" id="class" name="class" required>
                    </div>
                    <div class="form-group">
                      <label for="number">Number</label>
                      <input type="number" class="form-control" id="number" name="number" required>
                    </div>
                    <div class="form-group">
                      <label for="photo">Photo</label>
                      <input type="file" class="form-control-file" id="photo" name="photo" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Register Candidate</button>
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

@app.route('/register_voter', methods=['POST'])
def register_voter():
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

@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    if 'admin_authenticated' not in session or not session['admin_authenticated']:
        flash("Please login as admin first!")
        return redirect(url_for('admin'))

    name = request.form['name']
    class_ = request.form['class']
    number = int(request.form['number'])
    photo = request.files['photo']

    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM candidates WHERE number = ?', (number,))
    if c.fetchone()[0] > 0:
        conn.close()
        flash("Candidate number already exists!")
        return redirect(url_for('admin'))

    if photo and allowed_file(photo.filename):
        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        photo_path = filename  # Store only the filename in the database

        c.execute('INSERT INTO candidates (name, class, number, photo) VALUES (?, ?, ?, ?)', (name, class_, number, photo_path))
        conn.commit()
        conn.close()

        flash("Candidate registered successfully!")
    else:
        flash("Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.")
        conn.close()
    return redirect(url_for('admin'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_authenticated', None)
    flash("Logged out successfully!")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)