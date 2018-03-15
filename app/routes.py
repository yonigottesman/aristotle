from app import app
from flask import render_template, flash, redirect, url_for, jsonify
from app.forms import LoginForm
from flask_login import current_user, login_user
from flask_login import logout_user
from flask_login import login_required
from app.models import User, Run
from app.forms import RegistrationForm, AddRunForm
from app import db
from flask import request
from werkzeug.urls import url_parse


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = AddRunForm()
    if form.validate_on_submit():
        run = Run(description=form.description.data,
                  run_result=form.run_result.data, owner=current_user)
        db.session.add(run)
        db.session.commit()
        return redirect(url_for('index'))
    
    runs = current_user.runs.all()
    return render_template("index.html", title='Home Page', runs=runs, form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# @app.route('/add_work', methods=['POST'])
# @login_required
# def add_work():
#     task_id = request.form['task_id']
#     add_amount = int(request.form['amount'])
#     task = Task.query.get(task_id)
#     task.progress = task.progress + add_amount
#     db.session.commit()
#     return jsonify({'new_progress':task.progress})
