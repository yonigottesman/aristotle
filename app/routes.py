from app import app
from flask import render_template, flash, redirect, url_for, jsonify
from app.forms import LoginForm
from flask_login import current_user, login_user
from flask_login import logout_user
from flask_login import login_required
from app.models import User, Run, Experiment
from app.forms import RegistrationForm, AddRunForm, AddExperimentForm
from app import db
from flask import request
from werkzeug.urls import url_parse


@app.route('/experiment/<experiment_id>', methods=['GET', 'POST'])
def experiment(experiment_id):

    Experiment.query.filter_by(id=experiment_id).first_or_404()
    
    form = AddRunForm()
    add_experiment_form = AddExperimentForm()
    if form.validate_on_submit():
        run = Run(description=form.description.data
                  , run_result=form.run_result.data, owner=current_user
                  , experiment_id=int(experiment_id))
        
        db.session.add(run)
        db.session.commit()
        return redirect(url_for('experiment',experiment_id=experiment_id))
    experiments = current_user.experiments.all()

    runs = current_user.runs.filter(Run.experiment_id==int(experiment_id))
    return render_template("index.html", title='Home Page', runs=runs, form=form
                           , add_experiment_form=add_experiment_form
                           , experiments=experiments
                           , experiment_id=int(experiment_id))
    

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():

    add_experiment_form = AddExperimentForm()
    experiments = current_user.experiments.all()

    return render_template("index.html", title='Home Page', runs=None, form=None
                           , add_experiment_form=add_experiment_form
                           , experiments=experiments)



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


@app.route('/add_experiment', methods=['GET', 'POST'])
def add_experiment():
    form = AddExperimentForm()
    if form.validate_on_submit():
        experiment = Experiment(description=form.description.data
                                , owner=current_user)
        db.session.add(experiment)
        db.session.commit()
        return redirect(url_for('experiment', experiment_id=experiment.id))
    
    #TODO flash an error?
    return redirect(url_for('index'))    
