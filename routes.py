from flask import render_template, url_for,redirect,flash,request,session
from datetime import datetime,date
from app import app
from models import db, User, Subject, Chapter, Quiz, Question, Scores
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timezone, timedelta

def get_ist_time():
    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST)

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


def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash("You are not authorized to access this page")
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

#--------------------LOGIN--------------------#

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

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


#-----------------REGISTER-------------------#

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


#---------------PROFILE-------------------#

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

#---------------SCORES-------------------#

@app.route('/scores')
@auth_required
def scores():
    current_user = User.query.get(session.get('user_id'))
    if not current_user:
        flash("User session expired. Please log in again.", "danger")
        return redirect(url_for('login'))
    if current_user.is_admin:
        all_scores = Scores.query.all()
        return render_template('admin_scores.html', scores=all_scores)
    else:
        user_scores = Scores.query.filter_by(user_id=current_user.id).all()
        return render_template('user_scores.html', scores=user_scores)



#---------------LOGOUT-------------------#

@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    flash('Logged out successfully')
    return redirect(url_for('login'))


#--------------ADMIN PAGES-----------------#
@app.route('/admin')
@admin_required
def admin():
    subjects = Subject.query.all()
    return render_template('admin.html', subjects=subjects)


#-------------------ADD SUBJECTS-------------------#

@app.route('/subject/add')
@admin_required
def add_subject():
    return render_template('subject/add.html')

@app.route('/subject/add', methods=['POST'])
@admin_required
def add_subject_post():
    sub_name = request.form.get('sub_name')
    sub_desc = request.form.get('sub_desc')

    if not sub_name:
        flash("Please enter subject name")
        return redirect(url_for('add_subject'))

    subject = Subject(name=sub_name, desc=sub_desc)
    db.session.add(subject)
    db.session.commit()

    flash("Subject added successfully")
    return redirect(url_for('admin'))

#-------------------SHOW SUBJECT-------------------#

@app.route('/subject/<int:id>')
@admin_required
def show_subject(id):
    subject = Subject.query.get(id)
    if not subject:
        flash("Subject does not exist")
        return redirect(url_for('admin'))
    return render_template('subject/show.html', subject=subject)

#-------------------EDIT SUBJECTS-------------------#

@app.route('/subject/<int:id>/edit')
@admin_required
def edit_subject(id):
    subject = Subject.query.get(id)
    if not subject:
        flash("Subject does not exist")
        return redirect(url_for('admin'))
    return render_template('subject/edit.html', subject=subject)


@app.route('/subject/<int:id>/edit', methods=['POST'])
@admin_required
def edit_subject_post(id):
    subject = Subject.query.get(id)
    if not subject:
        flash("Subject does not exist")
        return redirect(url_for('admin'))

    sub_name = request.form.get('sub_name')
    sub_desc = request.form.get('sub_desc')
    if not sub_name:
        flash("Please fill out subject name")
        return redirect(url_for('edit_subject', id=id))
    subject.name = sub_name
    subject.desc = sub_desc
    db.session.commit()
    flash("Subject updated successfully")
    return redirect(url_for('admin'))


#-------------------DELETE SUBJECTS-------------------#

@app.route('/subject/<int:id>/delete')
@admin_required
def delete_subject(id):
    subject = Subject.query.get(id)
    if not subject:
        flash("Subject does not exist!")
        return redirect(url_for('admin'))
    return render_template('subject/delete.html', subject=subject)


@app.route('/subject/<int:id>/delete', methods=['POST'])
@admin_required
def delete_subject_post(id):
    subject = Subject.query.get(id)
    if not subject:
        flash("Subject does not exist!")
        return redirect(url_for('admin'))
    db.session.delete(subject)
    db.session.commit()

    flash("Subject deleted successfully")
    return redirect(url_for('admin'))


#------------------ CHAPTERS --------------------#


#-------------------ADD CHAPTER-------------------#
@app.route('/chapter/add/<int:subject_id>')
@admin_required
def add_chapter(subject_id):
    subject = Subject.query.get(subject_id)
    subjects = Subject.query.all()
    if not subject:
        flash("Subject does not exist")
        return redirect(url_for('admin'))
    return render_template('chapter/add.html', subject=subject, subjects=subjects)

@app.route('/chapter/add/<int:subject_id>', methods=['POST'])
@admin_required
def add_chapter_post(subject_id):
    subject = Subject.query.get(subject_id)
    if not subject:
        flash("Subject does not exist")
        return redirect(url_for('admin'))

    chap_name = request.form.get('chap_name')
    chap_desc = request.form.get('chap_desc')

    if not chap_name:
        flash("Please enter chapter name")
        return redirect(url_for('add_chapter', subject_id = subject_id))

    chapter = Chapter(name=chap_name, desc=chap_desc, sub_id=subject_id)
    db.session.add(chapter)
    db.session.commit()

    flash("Chapter added successfully")
    return redirect(url_for('show_subject', id=subject_id))

#-------------------EDIT CHAPTER-------------------#

@app.route('/chapter/<int:chapter_id>/edit')
@admin_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    subjects = Subject.query.all()
    if not chapter:
        flash("Chapter does not exist")
        return redirect(url_for('admin'))
    return render_template('chapter/edit.html', chapter=chapter, subjects=subjects)


@app.route('/chapter/<int:chapter_id>/edit', methods=['POST'])
@admin_required
def edit_chapter_post(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        flash("Chapter does not exist")
        return redirect(url_for('admin'))

    chap_name = request.form.get('chap_name')
    chap_desc = request.form.get('chap_desc')
    chap_sub = request.form.get('subject_id')
    if not chap_name:
        flash("Please fill out chapter name")
        return redirect(url_for('edit_chapter', chapter_id=chapter_id))
    chapter.name = chap_name
    chapter.desc = chap_desc
    chapter.sub_id = int(chap_sub) if chap_sub else chapter.sub_id
    db.session.commit()
    flash("Chapter updated successfully")
    return redirect(url_for('show_subject', id=chapter.sub_id))


#--------------DELETE CHAPTER--------------#


@app.route('/chapter/<int:chapter_id>/delete')
@admin_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        flash("Chapter does not exist!")
        return redirect(url_for('admin'))
    return render_template('chapter/delete.html', chapter=chapter)


@app.route('/chapter/<int:chapter_id>/delete', methods=['POST'])
@admin_required
def delete_chapter_post(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        flash("Chapter does not exist!")
        return redirect(url_for('admin'))
    sub_id = chapter.sub_id
    db.session.delete(chapter)
    db.session.commit()

    flash("Chapter deleted successfully")
    return redirect(url_for('show_subject', id=sub_id))


#--------------SHOW CHAPTER--------------#

@app.route('/chapter/<int:chapter_id>')
@admin_required
def show_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        flash("Chapter does not exist!")
        return redirect(url_for('admin'))
    return render_template('chapter/show.html', chapter=chapter)


#--------------QUIZZES---------------------#

#--------------ADD QUIZ--------------------#

@app.route('/quiz/add/<int:chapter_id>')
@admin_required
def add_quiz(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    chapters = Chapter.query.all()
    if not chapter:
        flash("Chapter does not exist")
        return redirect(url_for('show_subject', id=chapter.sub_id))
    return render_template('quiz/add.html', chapter=chapter, chapters=chapters)

@app.route('/quiz/add/<int:chapter_id>', methods=['POST'])
@admin_required
def add_quiz_post(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    chapters = Chapter.query.all()
    if not chapter:
        flash("Chapter does not exist")
        return redirect(url_for('show_subject', id=chapter.sub_id))

    quiz_name = request.form.get('quiz_name')
    quiz_dur = request.form.get('quiz_dur')
    today = date.today()

    if not quiz_name:
        flash("Please enter quiz name")
        return redirect(url_for('add_quiz', chapter_id = chapter_id))


    quiz = Quiz(name=quiz_name, chap_id=chapter_id, duration=quiz_dur, pub_date=today)
    db.session.add(quiz)
    db.session.commit()

    flash("Quiz added successfully")
    return redirect(url_for('show_chapter', chapter_id=quiz.chap_id))


#-------------- EDIT QUIZ--------------------#

@app.route('/quiz/<int:quiz_id>/edit')
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    chapters = Chapter.query.all()
    if not quiz:
        flash("Quiz does not exist")
        return redirect(url_for('admin'))
    return render_template('quiz/edit.html', chapters=chapters, quiz=quiz)


@app.route('/quiz/<int:quiz_id>/edit', methods=['POST'])
@admin_required
def edit_quiz_post(quiz_id):
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        flash("Quiz does not exist")
        return redirect(url_for('admin'))

    quiz_name = request.form.get('quiz_name')
    quiz_dur = request.form.get('quiz_dur')
    quiz_chap = request.form.get('chapter_id')
    today = date.today()

    if not quiz_name:
        flash("Please enter quiz name")
        return redirect(url_for('add_quiz', chapter_id = quiz.chap_id))
    quiz.name = quiz_name
    quiz.duration = int(quiz_dur) if quiz_dur else quiz.duration
    quiz.chap_id = int(quiz_chap) if quiz_chap else quiz.chap_id
    db.session.commit()
    flash("Quiz updated successfully")
    return redirect(url_for('show_chapter', chapter_id=quiz.chap_id))


#--------------DELETE QUIZ--------------#


@app.route('/quiz/<int:quiz_id>/delete')
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz does not exist!")
        return redirect(url_for('admin'))
    return render_template('quiz/delete.html', quiz=quiz)


@app.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@admin_required
def delete_quiz_post(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz does not exist!")
        return redirect(url_for('admin'))
    chap_id = quiz.chap_id
    db.session.delete(quiz)
    db.session.commit()

    flash("Quiz deleted successfully")
    return redirect(url_for('show_chapter', chapter_id=chap_id))


#--------------SHOW QUIZ--------------#

@app.route('/quiz/<int:quiz_id>')
@admin_required
def show_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz does not exist!")
        return redirect(url_for('admin'))
    return render_template('quiz/show.html', quiz=quiz)


#--------------QUESTIONS----------------#

#--------------ADD QUESTIONS------------#

@app.route('/question/add/<int:quiz_id>')
@admin_required
def add_question(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    quizzes = Quiz.query.all()
    if not quiz:
        flash("Quiz does not exist")
        return redirect(url_for('show_chapter', chapter_id=quiz.chap_id))
    return render_template('question/add.html', quiz=quiz, quizzes=quizzes)

@app.route('/question/add/<int:quiz_id>', methods=['POST'])
@admin_required
def add_question_post(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    quizzes = Quiz.query.all()
    if not quiz:
        flash("Quiz does not exist")
        return redirect(url_for('show_chapter', chapter_id=quiz.chap_id))

    que_name = request.form.get('que_name')
    que = request.form.get('que')
    op1 = request.form.get('op1')
    op2 = request.form.get('op2')
    op3 = request.form.get('op3')
    op4 = request.form.get('op4')
    ans = request.form.get('ans')

    if not que_name or not que or not op1 or not op2 or not op3 or not op4 or not ans:
        flash("Please enter all details")
        return redirect(url_for('add_question', quiz_id = quiz_id))

    question = Question(name=que_name, q_statement=que, quiz_id=quiz_id, opt1=op1, opt2=op2, opt3= op3, opt4=op4, ans=ans)
    db.session.add(question)
    db.session.commit()
    flash("Question added successfully")

    return redirect(url_for('show_quiz', quiz_id=quiz_id))

#-------------- EDIT QUESTION--------------------#

@app.route('/question/<int:question_id>/edit')
@admin_required
def edit_question(question_id):
    question = Question.query.get(question_id)
    quizzes = Quiz.query.all()
    if not question:
        flash("Question does not exist")
        return redirect(url_for('admin'))
    return render_template('question/edit.html', quizzes=quizzes, question=question)


@app.route('/question/<int:question_id>/edit', methods=['POST'])
@admin_required
def edit_question_post(question_id):
    question = Question.query.get(question_id)
    quizzes = Quiz.query.all()
    if not question:
        flash("Question does not exist")
        return redirect(url_for('admin'))

    que_name = request.form.get('que_name') or question.name
    que = request.form.get('que') or question.q_statement
    op1 = request.form.get('op1') or question.opt1
    op2 = request.form.get('op2') or question.opt2
    op3 = request.form.get('op3') or question.opt3
    op4 = request.form.get('op4') or question.opt4
    ans = request.form.get('ans') or question.ans
    que_quiz = request.form.get('quiz_id') or question.quiz_id

    if not que_name:
        flash("Please enter question name")
        return redirect(url_for('add_question', quiz_id=question.quiz_id))

    question.name = que_name
    question.q_statement = que
    question.quiz_id = que_quiz
    question.opt1 = op1
    question.opt2 = op2
    question.opt3 = op3
    question.opt4 = op4
    question.ans = ans

    db.session.commit()
    flash("Question updated successfully")
    return redirect(url_for('show_quiz', quiz_id=question.quiz_id))


#--------------DELETE QUESTION--------------#


@app.route('/question/<int:question_id>/delete')
@admin_required
def delete_question(question_id):
    question = Question.query.get(question_id)
    if not question:
        flash("Question does not exist")
        return redirect(url_for('admin'))
    return render_template('question/delete.html', question=question)


@app.route('/question/<int:question_id>/delete', methods=['POST'])
@admin_required
def delete_question_post(question_id):
    question = Question.query.get(question_id)
    if not question:
        flash("Question does not exist")
        return redirect(url_for('admin'))
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()

    flash("Question deleted successfully")
    return redirect(url_for('show_quiz', quiz_id=quiz_id))


#--------------SHOW QUESTION--------------#

@app.route('/question/<int:question_id>')
@admin_required
def show_question(question_id):
    question = Question.query.get(question_id)
    quiz = Quiz.query.get(question.quiz_id)
    if not question:
        flash("Question does not exist!")
        return redirect(url_for('admin'))
    return render_template('question/show.html', question=question, quiz=quiz)


#-----------------USER PAGES---------------#

#-----------------INDEX---------------#


@app.route('/')
@auth_required
def index():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    subjects = Subject.query.all()
    return render_template('index.html', subjects=subjects)



@app.route('/subject/<int:subject_id>/chapter/<int:chapter_id>')
@auth_required
def view_chapter(subject_id, chapter_id):
    subject = Subject.query.get(subject_id)
    chapter = Chapter.query.get(chapter_id)
    quizzes = chapter.quizzes
    return render_template('user_chapter.html', subject=subject, chapter=chapter, quizzes=quizzes)


@app.route('/quiz/<int:quiz_id>/start')
@auth_required
def start_quiz(quiz_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("User session expired. Please log in again.", "danger")
        return redirect(url_for('login'))

    quiz = Quiz.query.get_or_404(quiz_id)

    # Check if the user has already attempted the quiz
    existing_attempt = Scores.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
    if existing_attempt:
        flash("You have already attempted this quiz.", "warning")
        return redirect(url_for('view_chapter', subject_id=quiz.chapter.sub_id, chapter_id=quiz.chap_id))

    # Store quiz start time in session
    session[f'quiz_{quiz_id}_start_time'] = get_ist_time().isoformat()

    return render_template('start_quiz.html', quiz=quiz, questions=quiz.questions)


@app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@auth_required
def submit_quiz(quiz_id):
    current_user = User.query.get(session.get('user_id'))
    if not current_user:
        flash("User session expired. Please log in again.", "danger")
        return redirect(url_for('login'))

    quiz = Quiz.query.get_or_404(quiz_id)

    # Ensure quiz start time exists
    start_time_str = session.get(f'quiz_{quiz_id}_start_time')
    if not start_time_str:
        flash("Quiz has not been started.", "danger")
        return redirect(url_for('view_chapter', subject_id=quiz.chapter.sub_id, chapter_id=quiz.chap_id))

    start_time = datetime.fromisoformat(start_time_str)
    elapsed_time = (get_ist_time() - start_time).total_seconds()

    # Validate quiz duration
    if elapsed_time > quiz.duration * 60:
        flash("Time is up! Your submission was not accepted.", "danger")
        return redirect(url_for('view_chapter', subject_id=quiz.chapter.sub_id, chapter_id=quiz.chap_id))

    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    if not questions:
        flash("This quiz has no questions.", "warning")
        return redirect(url_for('view_chapter', subject_id=quiz.chapter.sub_id, chapter_id=quiz.chap_id))

    # Check if the user already submitted
    existing_attempt = Scores.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    if existing_attempt:
        flash("You have already submitted this quiz.", "warning")
        return redirect(url_for('view_chapter', subject_id=quiz.chapter.sub_id, chapter_id=quiz.chap_id))

    user_answers = {}
    score = 0

    for question in questions:
        selected_option = request.form.get(f'question_{question.id}')
        if selected_option:
            user_answers[question.id] = int(selected_option)
            if int(selected_option) == question.ans:
                score += 1
        else:
            user_answers[question.id] = None

    # Save the score
    new_score = Scores(
        user_id=current_user.id,
        quiz_id=quiz_id,
        total_score=score,
        datetime=get_ist_time()
    )
    db.session.add(new_score)
    db.session.commit()

    return render_template(
        'submit_quiz.html',
        quiz=quiz,
        score=score,
        total_questions=len(questions),
        questions=questions,
        user_answers=user_answers
    )


@app.route('/quizzes', methods=['GET'])
@auth_required
def search_quizzes():
    subject_name = request.args.get('subject_name', '').strip()
    chapter_name = request.args.get('chapter_name', '').strip()
    quiz_name = request.args.get('quiz_name', '').strip()

    # Start with all quizzes
    query = Quiz.query

    # Filter by subject name if provided
    if subject_name:
        query = query.join(Chapter).join(Subject).filter(Subject.name.ilike(f"%{subject_name}%"))

    # Filter by chapter name if provided
    if chapter_name:
        query = query.join(Chapter).filter(Chapter.name.ilike(f"%{chapter_name}%"))

    # Filter by quiz name if provided
    if quiz_name:
        query = query.filter(Quiz.name.ilike(f"%{quiz_name}%"))

    # Fetch filtered quizzes
    quizzes = query.all()

    user = User.query.get(session.get('user_id'))

    if user.is_admin:
        return render_template('admin_quizzes.html', quizzes=quizzes)

    return render_template('quizzes.html', quizzes=quizzes)
