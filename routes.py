from flask import render_template, url_for,redirect,flash,request,session
from datetime import datetime
from app import app
from models import db, User, Subject, Chapter, Quiz, Question, Scores
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps


#decorator for auth_required
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please log in to continue')
            return redirect(url_for('login'))
    return inner

#-------------------


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')



@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')



@app.route('/register')
def register():
    return render_template('register.html')



@app.route('/register', methods=['POST'])
def register_post():
    full_name = request.form.get('full_name')
    username = request.form.get('username')
    password = request.form.get('password')
    qualification = request.form.get('qualification')
    dob = request.form.get('dob')
    dob_obj = None if not dob else datetime.strptime(dob, "%Y-%m-%d").date()  # Convert string to date

    if not username or not password:
        flash("Please fill out all fields")
        return redirect(url_for('register'))

    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register'))

    password_hash = generate_password_hash(password)

    new_user = User(username=username, passhash=password_hash, name=full_name,dob=dob_obj, qualification=qualification)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))



@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')


    if not username or not password:
        flash("Please fill out all fields")
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No such username found')
        return redirect(url_for('login'))

    if not check_password_hash(user.passhash,password):
        flash("Incorrect Password")
        return redirect(url_for('login'))

    session['user_id'] = user.id
    flash('Login Successful')
    return redirect(url_for('index'))



@app.route('/profile')
@auth_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')

    user = User.query.get(session['user_id'])

    if not username or not cpassword:
        flash('Please fill out all required fields')
        return redirect(url_for('profile'))

    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('profile'))

    if username != user.username:
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('profile'))

    user.username = username
    user.name = name

    if password:
        user.passhash = generate_password_hash(password)

    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))



@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    flash('Logged out successfully')
    return redirect(url_for('login'))

