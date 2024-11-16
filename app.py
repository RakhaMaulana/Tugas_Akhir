from flask import Flask, request, render_template_string, redirect, url_for
from main import poll_machine
from createdb import insert_voter

app = Flask(__name__)
pm = poll_machine()

ADMIN_PASSWORD = "admin123"  # Simple admin password for demonstration

@app.route('/')
def index():
    return render_template_string('''
        <form action="/vote" method="post">
            Poll Answer: <input type="text" name="poll_answer"><br>
            ID Number: <input type="number" name="id_number"><br>
            <input type="submit" value="Submit">
        </form>
    ''')

@app.route('/vote', methods=['POST'])
def vote():
    poll_answer = request.form['poll_answer']
    id_number = int(request.form['id_number'])
    pm.start_poll(poll_answer, id_number)
    return "Vote submitted! Check the CLI for details."

@app.route('/admin')
def admin():
    return render_template_string('''
        <form action="/register" method="post">
            Admin Password: <input type="password" name="password"><br>
            Voter ID: <input type="number" name="voter_id"><br>
            <input type="submit" value="Register Voter">
        </form>
    ''')

@app.route('/register', methods=['POST'])
def register():
    password = request.form['password']
    if password != ADMIN_PASSWORD:
        return "Unauthorized access!", 403

    voter_id = int(request.form['voter_id'])
    insert_voter(voter_id)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)