from app import app
from flask import render_template, flash, redirect, url_for, jsonify
from app.forms import LoginForm
from flask_login import current_user, login_user
from flask_login import logout_user
from flask_login import login_required
from app.models import User, Run, Experiment
from app.forms import RegistrationForm, AddRunForm, AddExperimentForm, EditExperimentForm, EditRunForm
from app import db
from flask import request
from werkzeug.urls import url_parse
from RestrictedPython import compile_restricted
from AccessControl.ZopeGuards import get_safe_globals


@login_required
@app.route('/experiment/<experiment_id>/run/<run_id>', methods=['GET', 'POST'])
def run(experiment_id,run_id):
    run = Run.query.filter_by(id=run_id, user_id=current_user.id).first_or_404()
    
    form = EditRunForm()
    if form.validate_on_submit():
        if form.delete.data == True:
            db.session.delete(run)
            db.session.commit()
            return redirect(url_for('experiment', experiment_id=experiment_id))
        else:
            if form.description.data != '':
                run.description = form.description.data
            if form.columns.data != '':
                if validat_csv(form.columns.data) == False:
                    flash('columns wrongs format: ' + form.columns.data)
                    return redirect(url_for('run',experiment_id=experiment_id,run_id=run_id))
                run.columns = form.columns.data
            if form.run_result.data != '':
                run.run_result = form.run_result.data
                
            db.session.add(run)
            db.session.commit()
            return redirect(url_for('experiment', experiment_id=experiment_id))
        
    add_experiment_form = AddExperimentForm()
    experiments = current_user.experiments.all()

    run = Run.query.get(run_id)

    return render_template("run.html", title='Run', form=form
                           , add_experiment_form=add_experiment_form
                           , experiments=experiments
                           , run=run)    

def validat_csv(line):
    if line is None:
        return True
    for i in line.split(','):
        if i.strip() != '':
            if len(i.split('=')) != 2:
                return False
    return True


def create_experiment_table(experiment_id):
    runs = current_user.runs.filter(Run.experiment_id==int(experiment_id))
    column_names = []
    run_columns_dict = {}
    for run in runs:
        columns_raw = run.columns.split(',')
        column_dict = {}
        for column_raw in columns_raw:
            if column_raw != '':
                name = column_raw.split('=')[0].strip()
                value = column_raw.split('=')[1].strip()
                if name not in column_names:
                    column_names.append(name)
                column_dict[name] = value
        run_columns_dict[run] = column_dict

    table = []
        
    # Now expand all run to have all column_names and set irelevant '-'
    for run in runs:
        defaults = dict([(name, '-') for name in column_names])
        defaults.update(run_columns_dict[run])
        run_columns_dict[run] = defaults
        table.append({'run_id':run.id, 'columns':list(defaults.values())})

    return [column_names] + table


@login_required
@app.route('/experiment/<experiment_id>', methods=['GET', 'POST'])
def experiment(experiment_id):

    experiment = Experiment.query.filter_by(id=experiment_id).first_or_404()
    form = AddRunForm()
    if form.validate_on_submit():
        columns = ''
        if experiment.column_extract_code is not None:
            # TODO This part should be done once when code is submitted.
            source_code = experiment.column_extract_code
            byte_code = compile_restricted(source_code, filename='<inline code>', mode='exec')
            loc = {}
            exec(byte_code,get_safe_globals(),loc)
            columns = loc['parse'](form.run_result.data)
            if columns is None:
                columns = ''
            
            if validat_csv(columns) == False:
                flash('exctracted columns wrongs format: ' + columns)
                return redirect(url_for('experiment',experiment_id=experiment_id))

        if validat_csv(form.columns.data) == False:
            flash('columns wrongs format: ' + form.columns.data)
            return redirect(url_for('experiment',experiment_id=experiment_id))

        if columns == '':
            columns = form.columns.data
        else:
            columns = columns + form.columns.data

        run = Run(description=form.description.data
                  , run_result=form.run_result.data, owner=current_user
                  , columns=columns
                  , experiment_id=int(experiment_id))
            
        db.session.add(run)
        db.session.commit()

        return redirect(url_for('experiment',experiment_id=experiment_id))
    
    experiments = current_user.experiments.all()

    t = create_experiment_table(experiment_id)
    table = t[1:]
    columns = t[0]
        
    add_experiment_form = AddExperimentForm()

    return render_template("experiment.html", title='Experiment', form=form
                           , add_experiment_form=add_experiment_form
                           , experiments=experiments
                           , experiment_id=int(experiment_id)
                           , columns=columns
                           , table=table
                           , column_range=range(len(columns)))
    

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


@login_required
@app.route('/add_experiment', methods=['GET', 'POST'])
def add_experiment():
    form = AddExperimentForm()
    if form.validate_on_submit():
        experiment = Experiment(description=form.description.data
                                , owner=current_user
                                , columns='')
        db.session.add(experiment)
        db.session.commit()
        return redirect(url_for('experiment', experiment_id=experiment.id))
    
    #TODO flash an error?
    return redirect(url_for('index'))    


@app.route('/experiment/<experiment_id>/settings', methods=['GET', 'POST'])
@login_required
def experiment_settings(experiment_id):

    experiment = Experiment.query.filter_by(id=experiment_id).first_or_404()
    form = EditExperimentForm()
    if form.validate_on_submit():
        if form.delete.data == True:
            db.session.delete(experiment)
            db.session.commit()
            return redirect(url_for('index'))        
        else:
            if form.description.data != '':
                experiment.description = form.description.data
            if form.columns.data != '':
                experiment.columns = form.columns.data
            if form.column_extract_code.data != '':
                experiment.column_extract_code = form.column_extract_code.data
                
            db.session.add(experiment)
            db.session.commit()
            return redirect(url_for('experiment', experiment_id=experiment_id))        
    else:
        experiments = current_user.experiments.all()
        add_experiment_form = AddExperimentForm()        

        return render_template("experiment_settings.html", title='Settings', form=form
                               , experiments=experiments
                               , add_experiment_form=add_experiment_form
                               , experiment_id=int(experiment_id)
                               ,experiment=experiment)

    
