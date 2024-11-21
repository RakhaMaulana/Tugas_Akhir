from flask import Flask, request, render_template_string, redirect, url_for, flash, session, send_from_directory, abort
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import sqlite3
import bcrypt
from main import poll_machine  # Import poll_machine
from createdb import insert_voter  # Import insert_voter
import base64
import time
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages and session management
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1 GB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

CORS(app)  # Enable CORS

pm = poll_machine()  # Initialize poll_machine

@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(e):
    flash("File is too large. Maximum upload size is 1 GB.")
    return redirect(url_for('index'))

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

def is_valid_voter(self, id_number):
    """Memeriksa apakah ID terdaftar dan belum memberikan suara"""
    conn = self.get_db_connection()
    c = conn.cursor()
    c.execute('SELECT has_voted, status FROM voters WHERE id_number = ?', (id_number,))
    result = c.fetchone()
    conn.close()
    if result is None:
        print("ID number tidak terdaftar.")
        return False
    elif result[1] != 'approved':
        print("ID number belum disetujui.")
        return False
    elif result[0]:
        print("ID number sudah melakukan voting.")
        return False
    return True

def get_db_connection():
    conn = sqlite3.connect('voting.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    candidates = get_candidates()
    return render_template_string('''
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet">
            <title>Vote</title>
            <style>
              body {
                background-color: #f8f9fa;
              }
              .navbar-brand {
                font-weight: bold;
                font-size: 1.5rem;
              }
              .hero-section {
                background: linear-gradient(to right, #6a11cb, #2575fc);
                color: #fff;
                padding: 50px 0;
                text-align: center;
                border-radius: 8px;
              }
              .hero-section h1 {
                font-size: 2.5rem;
              }
              .hero-section p {
                font-size: 1.2rem;
              }
              .candidate-photo {
                max-width: 200px;
                margin-top: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
              }
              .candidate-info {
                text-align: center;
                margin: 20px 0;
              }
              .form-container {
                background: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                padding: 20px;
                max-width: 600px;
                margin: auto;
              }
              .btn-block {
                margin-top: 15px;
              }
              footer {
                margin-top: 30px;
                text-align: center;
                color: #6c757d;
              }
            </style>
          </head>
          <body>
            <nav class="navbar navbar-expand-lg navbar-light bg-light">
              <div class="container">
                <a class="navbar-brand" href="#">Voting System</a>
                <div class="ml-auto">
                  <a href="/admin" class="btn btn-outline-primary btn-sm">Admin Login</a>
                </div>
              </div>
            </nav>
            <div class="container mt-4">
              <div class="hero-section">
                <h1>Your Vote Matters!</h1>
                <p>Make your voice heard by choosing the best candidate.</p>
              </div>
              <div class="form-container mt-4">
                {% if candidates %}
                <form action="/vote" method="post">
                  <div class="form-group">
                    <label for="id_number" class="form-label">ID Number</label>
                    <input type="number" class="form-control" id="id_number" name="id_number" required placeholder="Enter your ID number">
                  </div>
                  <div class="candidate-info">
                    <img id="candidate-photo" class="candidate-photo" src="{{ url_for('uploaded_file', filename=candidates[0][4]) }}" alt="Candidate Photo">
                    <h5 id="candidate-name">{{ candidates[0][1] }}</h5>
                    <p id="candidate-class">{{ candidates[0][2] }}</p>
                  </div>
                  <div class="form-group">
                    <label for="poll_answer" class="form-label">Select Candidate</label>
                    <select class="form-control" id="poll_answer" name="poll_answer" required onchange="updateCandidateInfo()">
                      {% for candidate in candidates %}
                        <option value="{{ candidate[3] }}" data-photo="{{ url_for('uploaded_file', filename=candidate[4]) }}" data-name="{{ candidate[1] }}" data-class="{{ candidate[2] }}">{{ candidate[3] }}</option>
                      {% endfor %}
                    </select>
                  </div>
                  <button type="submit" class="btn btn-primary btn-block">Submit Vote</button>
                </form>
                {% else %}
                <p class="text-center text-muted">No candidates available for voting.</p>
                {% endif %}
              </div>
            </div>
            <footer>
              <p>&copy; {{ year }} Voting System. All rights reserved.</p>
            </footer>
            <script>
              function updateCandidateInfo() {
                const select = document.getElementById('poll_answer');
                const selectedOption = select.options[select.selectedIndex];
                const photo = selectedOption.getAttribute('data-photo');
                const name = selectedOption.getAttribute('data-name');
                const classInfo = selectedOption.getAttribute('data-class');

                document.getElementById('candidate-photo').src = photo;
                document.getElementById('candidate-name').innerText = name;
                document.getElementById('candidate-class').innerText = classInfo;
              }

              // Initialize the first candidate
              if (document.getElementById('poll_answer').options.length > 0) {
                updateCandidateInfo();
              }
            </script>
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
          </body>
        </html>
    ''', candidates=candidates, year=time.strftime('%Y'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/vote', methods=['POST'])
def vote():
    poll_answer = request.form['poll_answer']
    id_number = int(request.form['id_number'])
    if not pm.p.is_valid_voter(id_number):
        flash("ID number tidak valid atau belum disetujui atau sudah digunakan untuk voting.")
        return redirect(url_for('index'))
    pm.start_poll(poll_answer, id_number)
    flash("Vote submitted successfully!")
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if 'admin_authenticated' in session and session['admin_authenticated']:
        # Check for session timeout
        if time.time() - session.get('last_activity', 0) > 900:  # 15 minutes
            session.pop('admin_authenticated', None)
            session.pop('last_activity', None)
            flash("Session expired. Please log in again.")
            return redirect(url_for('admin'))

        # Update last activity time
        session['last_activity'] = time.time()

        return render_template_string('''
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
                <title>Admin Dashboard</title>
                <style>
                  .container {
                    margin-top: 30px;
                  }
                  .section-header {
                    margin-top: 30px;
                    margin-bottom: 15px;
                  }
                </style>
              </head>
              <body>
                <nav class="navbar navbar-expand-lg navbar-light bg-light">
                  <div class="container-fluid">
                    <a class="navbar-brand" href="#">Voting System Admin</a>
                    <div>
                      <form action="{{ url_for('logout') }}" method="post" class="d-inline">
                        <button type="submit" class="btn btn-warning btn-sm">Logout</button>
                      </form>
                    </div>
                  </div>
                </nav>

                <div class="container">
                  <h1 class="text-center mb-4">Admin Dashboard</h1>

                  <!-- Register a Candidate Section -->
                  <div class="section-header">
                    <h3>Register a Candidate</h3>
                  </div>
                  <form action="/register_candidate" method="post" enctype="multipart/form-data" class="mb-4">
                    <div class="mb-3">
                      <label for="name" class="form-label">Candidate Name</label>
                      <input type="text" class="form-control" id="name" name="name" required>
                    </div>
                    <div class="mb-3">
                      <label for="class" class="form-label">Class</label>
                      <input type="text" class="form-control" id="class" name="class" required>
                    </div>
                    <div class="mb-3">
                      <label for="number" class="form-label">Number</label>
                      <input type="number" class="form-control" id="number" name="number" required>
                    </div>
                    <div class="mb-3">
                      <label for="photo" class="form-label">Photo</label>
                      <input type="file" class="form-control" id="photo" name="photo" accept="image/*" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Register Candidate</button>
                  </form>

                  <!-- Admin Actions Section -->
                  <div class="section-header">
                    <h3>Admin Actions</h3>
                  </div>
                  <a href="{{ url_for('admin_approve') }}" class="btn btn-info">Go to Admin Approval</a>
                </div>

                <!-- Flash Messages -->
                <div class="modal fade" id="flashModal" tabindex="-1" aria-labelledby="flashModalLabel" aria-hidden="true">
                  <div class="modal-dialog">
                    <div class="modal-content">
                      <div class="modal-header">
                        <h5 class="modal-title" id="flashModalLabel">Notification</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                      </div>
                      <div class="modal-body">
                        {% with messages = get_flashed_messages() %}
                          {% if messages %}
                            {% for message in messages %}
                              <p>{{ message }}</p>
                            {% endfor %}
                          {% endif %}
                        {% endwith %}
                      </div>
                      <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                      </div>
                    </div>
                  </div>
                </div>

                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
                <script>
                  document.addEventListener('DOMContentLoaded', function() {
                    {% with messages = get_flashed_messages() %}
                      {% if messages %}
                        var flashModal = new bootstrap.Modal(document.getElementById('flashModal'));
                        flashModal.show();
                      {% endif %}
                    {% endwith %}
                  });
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
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
                <title>Admin Login</title>
              </head>
              <body>
                <div class="container mt-5">
                  <h1 class="text-center">Admin Login</h1>
                  <form action="/admin_login" method="post" class="mt-3">
                    <div class="mb-3">
                      <label for="password" class="form-label">Admin Password</label>
                      <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Login</button>
                  </form>
                </div>
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
              </body>
            </html>
        ''')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form['password']
    password_hash = get_admin_password_hash()
    if bcrypt.checkpw(password.encode('utf-8'), password_hash):
        session['admin_authenticated'] = True
        session['last_activity'] = time.time()
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

    # Check for session timeout
    if time.time() - session.get('last_activity', 0) > 10:  # 15 minutes
        session.pop('admin_authenticated', None)
        session.pop('last_activity', None)
        flash("Session expired. Please log in again.")
        return redirect(url_for('admin'))

    # Update last activity time
    session['last_activity'] = time.time()

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

    # Check for session timeout
    if time.time() - session.get('last_activity', 0) > 900:  # 15 minutes
        session.pop('admin_authenticated', None)
        session.pop('last_activity', None)
        flash("Session expired. Please log in again.")
        return redirect(url_for('admin'))

    # Update last activity time
    session['last_activity'] = time.time()

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

@app.route('/admin_approve', methods=['GET', 'POST'])
def admin_approve():
    if 'admin_authenticated' not in session or not session['admin_authenticated']:
        flash("Please login as admin first!")
        return redirect(url_for('admin'))

    # Check for session timeout
    if time.time() - session.get('last_activity', 0) > 900:  # 15 minutes
        session.pop('admin_authenticated', None)
        session.pop('last_activity', None)
        flash("Session expired. Please log in again.")
        return redirect(url_for('admin'))

    # Update last activity time
    session['last_activity'] = time.time()

    if request.method == 'POST':
        id_number = int(request.form['id_number'])
        action = request.form['action']

        conn = sqlite3.connect('voting.db')
        c = conn.cursor()
        if action == 'approve':
            c.execute('UPDATE voters SET status = "approved" WHERE id_number = ?', (id_number,))
            flash(f"Voter {id_number} approved successfully!")
        elif action == 'reject':
            c.execute('DELETE FROM voters WHERE id_number = ?', (id_number,))
            flash(f"Voter {id_number} rejected successfully!")
        conn.commit()
        conn.close()
        return redirect(url_for('admin_approve'))

    conn = sqlite3.connect('voting.db')
    c = conn.cursor()
    c.execute('SELECT id_number, photo FROM voters WHERE status = "pending"')
    pending_voters = c.fetchall()
    conn.close()

    return render_template_string('''
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <title>Admin Approval</title>
            <style>
              .table th, .table td {
                vertical-align: middle;
              }
              .actions button {
                margin-right: 5px;
              }
              .no-data {
                text-align: center;
                padding: 50px 0;
                color: #6c757d;
                font-size: 1.2rem;
              }
            </style>
          </head>
          <body>
            <nav class="navbar navbar-expand-lg navbar-light bg-light">
              <div class="container-fluid">
                <a class="navbar-brand" href="#">Voting System Admin</a>
                <div>
                  <form action="{{ url_for('logout') }}" method="post" class="d-inline">
                    <button type="submit" class="btn btn-warning btn-sm">Logout</button>
                  </form>
                </div>
              </div>
            </nav>

            <div class="container my-4">
              <h1 class="text-center mb-4">Admin Approval</h1>

              <!-- Flash Messages -->
              {% with messages = get_flashed_messages() %}
                {% if messages %}
                  <div class="alert alert-info alert-dismissible fade show" role="alert">
                    {% for message in messages %}
                      <p class="mb-0">{{ message }}</p>
                    {% endfor %}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                  </div>
                {% endif %}
              {% endwith %}

              {% if pending_voters %}
                <table class="table table-bordered table-hover">
                  <thead class="table-light">
                    <tr>
                      <th>ID Number</th>
                      <th>Photo</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for voter in pending_voters %}
                      <tr>
                        <td>{{ voter[0] }}</td>
                        <td>
                          <img src="{{ url_for('uploaded_file', filename=voter[1]) }}" class="img-thumbnail" alt="Voter Photo" style="max-width: 120px;">
                        </td>
                        <td class="actions">
                          <form action="/admin_approve" method="post" class="d-inline">
                            <input type="hidden" name="id_number" value="{{ voter[0] }}">
                            <button type="submit" name="action" value="approve" class="btn btn-success btn-sm" title="Approve Voter">
                              ✔ Approve
                            </button>
                          </form>
                          <form action="/admin_approve" method="post" class="d-inline">
                            <input type="hidden" name="id_number" value="{{ voter[0] }}">
                            <button type="submit" name="action" value="reject" class="btn btn-danger btn-sm" title="Reject Voter">
                              ✖ Reject
                            </button>
                          </form>
                        </td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              {% else %}
                <div class="no-data">
                  <p>No pending voter registrations at the moment.</p>
                </div>
              {% endif %}
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
          </body>
        </html>
    ''', pending_voters=pending_voters)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_authenticated', None)
    session.pop('last_activity', None)
    flash("Logged out successfully!")
    return redirect(url_for('admin'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_number = int(request.form['id_number'])
        photo_data = request.form['photo_data']

        if not photo_data:
            flash("No photo data received. Please capture a photo.")
            return redirect(url_for('register'))

        try:
            # Decode the photo data and save it as an image file
            photo_filename = f"{id_number}.png"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            with open(photo_path, "wb") as photo_file:
                photo_file.write(base64.b64decode(photo_data.split(",")[1]))
        except (IndexError, ValueError) as e:
            flash("Failed to process photo data. Please try again.")
            return redirect(url_for('register'))

        retries = 5
        while retries > 0:
            try:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute('SELECT COUNT(*) FROM voters WHERE id_number = ?', (id_number,))
                    if c.fetchone()[0] > 0:
                        flash("ID number already registered. Please use a different ID number.")
                        return redirect(url_for('register'))

                    c.execute('INSERT INTO voters (id_number, photo, status) VALUES (?, ?, ?)', (id_number, photo_filename, 'pending'))
                    conn.commit()
                    break
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    retries -= 1
                    time.sleep(1)
                else:
                    raise
            finally:
                conn.close()

        if retries == 0:
            flash("Failed to register due to database lock. Please try again later.")
            return redirect(url_for('register'))

        flash("Registration submitted successfully! Please wait for admin approval.")
        return redirect(url_for('index'))

    return render_template_string('''
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <title>Register</title>
            <style>
              .form-section {
                margin-bottom: 30px;
              }
              #video, #canvas {
                    width: 100%;
                    max-width: 400px;
                    margin: 10px auto; /* Margin untuk memberi jarak antara elemen */
                    border: 2px solid #ddd;
                    border-radius: 10px;
                    display: block; /* Untuk memastikan elemen berada di tengah */
                }

                #canvas {
                    display: none; /* Hanya muncul setelah tombol capture ditekan */
                }
              .hero-section {
                background-color: #f8f9fa;
                padding: 50px 0;
                text-align: center;
                border-radius: 10px;
                margin-bottom: 30px;
              }
              .hero-section h1 {
                font-size: 2.5rem;
                font-weight: bold;
                color: #343a40;
              }
              .hero-section p {
                font-size: 1.2rem;
                color: #6c757d;
              }
              .form-container {
                max-width: 600px;
                margin: auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 10px;
                background-color: #fff;
              }
              .capture-button {
                margin-top: 20px;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <div class="hero-section">
                <h1>Register to Vote</h1>
                <p>Fill in your details and capture a photo to register.</p>
              </div>
              <div class="form-container">
                <form action="/register" method="post" class="mt-3">
                  <div class="form-group">
                    <label for="id_number">ID Number</label>
                    <input type="number" class="form-control" id="id_number" name="id_number" required>
                  </div>
                  <div class="form-group">
                      <label for="photo">Capture Photo</label>
                      <div class="text-center">
                          <video id="video" autoplay></video>
                          <div class="capture-button">
                              <button type="button" id="capture" class="btn btn-primary">Capture Photo</button>
                          </div>
                          <canvas id="canvas"></canvas>
                          <input type="hidden" name="photo_data" id="photo_data">
                      </div>
                  </div>
                  <button type="submit" class="btn btn-primary btn-block">Submit</button>
                </form>
              </div>
            </div>

            <!-- Modal -->
            <div class="modal fade" id="flashModal" tabindex="-1" aria-labelledby="flashModalLabel" aria-hidden="true">
              <div class="modal-dialog">
                <div class="modal-content">
                  <div class="modal-header">
                    <h5 class="modal-title" id="flashModalLabel">Notification</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                      <span aria-hidden="true">&times;</span>
                    </button>
                  </div>
                  <div class="modal-body">
                    {% with messages = get_flashed_messages() %}
                      {% if messages %}
                        {% for message in messages %}
                          <p>{{ message }}</p>
                        {% endfor %}
                      {% endif %}
                    {% endwith %}
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                  </div>
                </div>
              </div>
            </div>

            <script>
              // Access the webcam
              const video = document.getElementById('video');
              const canvas = document.getElementById('canvas');
              const captureButton = document.getElementById('capture');
              const photoDataInput = document.getElementById('photo_data');

              navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                  video.srcObject = stream;
                })
                .catch(err => {
                  console.error("Error accessing the webcam: " + err);
                });

              // Capture the photo
              captureButton.addEventListener('click', () => {
                const context = canvas.getContext('2d');
                const scale = 0.5;  // Scale down the image to reduce size
                canvas.width = video.videoWidth * scale;
                canvas.height = video.videoHeight * scale;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const photoData = canvas.toDataURL('image/png');
                photoDataInput.value = photoData;
                canvas.style.display = 'block';
              });

              // Show modal if there are flash messages
              $(document).ready(function() {
                {% with messages = get_flashed_messages() %}
                  {% if messages %}
                    $('#flashModal').modal('show');
                  {% endif %}
                {% endwith %}
              });
            </script>
            <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
            <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
          </body>
        </html>
    ''')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', debug=True)
