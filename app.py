from flask import Flask, request, render_template_string
from main import poll_machine

app = Flask(__name__)
pm = poll_machine()

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

if __name__ == '__main__':
    app.run(debug=True)