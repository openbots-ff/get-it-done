from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import re
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: the connection string after :// contains the following info:
# user:password@server:portNumber/databaseName

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://get-it-done:SHINee5252008@localhost:8889/get-it-done'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = '5252008'

class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    completed = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, name, owner):
        self.name = name
        self.completed = False
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    tasks = db.relationship('Task', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.pw_hash = make_pw_hash(password)    

@app.before_request
def require_login():
    allowed_routes = ['login', 'register']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect("/login")


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']
        user = User.query.filter_by(email=user_email).first()
        
        if user and check_pw_hash(user_password, user.pw_hash):
            session['email'] = user_email
            flash("Logged in")
            return redirect("/") 
        else:
            flash("User password incorrect or user does not exist", "error")
            

    return render_template("login.html")

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_email = request.form['email']
        user_password = request.form['password']
        user_verify = request.form['verify']

        if not (re.match(r"^.{3,20}$", user_email) and re.match(r"^\w+@\w+\.\w+$", user_email)):
            flash("That's not a valid email", "error")
        if not re.match(r"^\w{3,20}$", user_password):
            flash("That's not a valid password", "error")
        if user_password != user_verify:
            flash("Passwords don't match", "error")
        if re.match(r"^.{3,20}$", user_email) and re.match(r"^\w+@\w+\.\w+$", user_email) and re.match(r"^\w{3,20}$", user_password) and user_password == user_verify:
            existing_user = User.query.filter_by(email=user_email).first()
            if not existing_user:
                new_user = User(user_email, user_password)
                db.session.add(new_user)
                db.session.commit()
                session['email'] = user_email
                flash("Registration complete!")
                return redirect("/")
            else:
                flash("This user already exists", "error")

    return render_template("register.html")

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')


@app.route('/', methods=['POST', 'GET'])
def index():
    task_owner = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        task_name = request.form['task']
        new_task = Task(task_name, task_owner)
        db.session.add(new_task)
        db.session.commit()

    tasks = Task.query.filter_by(completed = False, owner=task_owner).all()
    completed_tasks = Task.query.filter_by(completed = True, owner=task_owner).all()

    return render_template('todos.html', title="Get It Done!", tasks=tasks, 
        completed_tasks=completed_tasks)

@app.route("/delete-task", methods=['POST'])
def delete_task():
    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    task.completed = True
    db.session.add(task)
    db.session.commit()

    return redirect('/')


if __name__ == '__main__':
    app.run()