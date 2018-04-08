from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Run, Experiment
from app.main.forms import AddRunForm, AddExperimentForm, EditExperimentForm, EditRunForm
from app import db
from werkzeug.urls import url_parse
from RestrictedPython import compile_restricted
from AccessControl.ZopeGuards import get_safe_globals
from app.main import bp


@login_required
@bp.route('/experiment/<experiment_id>/compare', methods=['GET', 'POST'])
def compare(experiment_id):
    run1_id = request.args.get('run1')
    run2_id = request.args.get('run2')
    run1 = Run.query.filter_by(id=run1_id, user_id=current_user.id).first_or_404()
    run2 = Run.query.filter_by(id=run2_id, user_id=current_user.id).first_or_404()
    
    return render_template("compare.html", run1=run1,run2=run2)


@login_required
@bp.route('/experiment/<experiment_id>/select_compare', methods=['GET', 'POST'])
def select_compare(experiment_id):
    # TODO change this form to wtfform if possible
    selected_run_ids = request.form.getlist('rowid')
    if len(selected_run_ids) != 2:
        flash('Select 2 for comparison!')
        return redirect(url_for('main.experiment',experiment_id=experiment_id))
    
    u = url_for('main.compare', experiment_id=experiment_id) + '?run1=' + selected_run_ids[0] + '&run2=' + selected_run_ids[1]
    return redirect(u)

    
@login_required
@bp.route('/experiment/<experiment_id>/run/<run_id>', methods=['GET', 'POST'])
def run(experiment_id,run_id):
    run = Run.query.filter_by(id=run_id, user_id=current_user.id).first_or_404()
    
    form = EditRunForm()
    if form.validate_on_submit():
        if form.delete.data == True:
            db.session.delete(run)
            db.session.commit()
            return redirect(url_for('main.experiment', experiment_id=experiment_id))
        else:
            if form.description.data != '':
                run.description = form.description.data
            if form.columns.data != '':
                if validat_csv(form.columns.data) == False:
                    flash('columns wrongs format: ' + form.columns.data)
                    return redirect(url_for('main.run',experiment_id=experiment_id,run_id=run_id))
                run.columns = form.columns.data
            if form.run_result.data != '':
                run.run_result = form.run_result.data
                
            db.session.add(run)
            db.session.commit()
            return redirect(url_for('main.experiment', experiment_id=experiment_id))
        
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
        print(run.columns.split(','),flush=True)
        columns_raw = run.columns.split(',')
        column_dict = {}
        for column_raw in columns_raw:
            if column_raw.strip() != '':
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


def clean_columns(columns_csv):
    cleaned = []
    for column in columns_csv.split(','):
        if column.strip() != '':
            key = column.split('=')[0].strip()
            value = column.split('=')[1].strip()
            cleaned.append(key+'='+value)
    return ', '.join(cleaned)


@login_required
@bp.route('/experiment/<experiment_id>', methods=['GET', 'POST'])
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
                return redirect(url_for('main.experiment',experiment_id=experiment_id))
            columns = clean_columns(columns)
            
        if validat_csv(form.columns.data) == False:
            flash('columns wrongs format: ' + form.columns.data)
            return redirect(url_for('main.experiment',experiment_id=experiment_id))
        
        if columns == '':
            columns = clean_columns(form.columns.data)
        else:
            columns = columns + ', ' + clean_columns(form.columns.data)

        run = Run(description=form.description.data
                  , run_result=form.run_result.data, owner=current_user
                  , columns=columns
                  , experiment_id=int(experiment_id))
            
        db.session.add(run)
        db.session.commit()

        return redirect(url_for('main.experiment',experiment_id=experiment_id))
    
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
    

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():

    add_experiment_form = AddExperimentForm()
    experiments = current_user.experiments.all()

    return render_template("index.html", title='Home Page', runs=None, form=None
                           , add_experiment_form=add_experiment_form
                           , experiments=experiments)


@login_required
@bp.route('/add_experiment', methods=['GET', 'POST'])
def add_experiment():
    form = AddExperimentForm()
    if form.validate_on_submit():
        experiment = Experiment(description=form.description.data
                                , owner=current_user
                                , columns='')
        db.session.add(experiment)
        db.session.commit()
        return redirect(url_for('main.experiment', experiment_id=experiment.id))
    
    #TODO flash an error?
    return redirect(url_for('main.index'))    


@bp.route('/experiment/<experiment_id>/settings', methods=['GET', 'POST'])
@login_required
def experiment_settings(experiment_id):

    experiment = Experiment.query.filter_by(id=experiment_id).first_or_404()
    form = EditExperimentForm()
    if form.validate_on_submit():
        if form.delete.data == True:
            db.session.delete(experiment)
            db.session.commit()
            return redirect(url_for('main.index'))        
        else:
            if form.description.data != '':
                experiment.description = form.description.data
            if form.columns.data != '':
                experiment.columns = form.columns.data
            if form.column_extract_code.data != '':
                experiment.column_extract_code = form.column_extract_code.data
                
            db.session.add(experiment)
            db.session.commit()
            return redirect(url_for('main.experiment', experiment_id=experiment_id))        

    experiments = current_user.experiments.all()
    add_experiment_form = AddExperimentForm()
    if experiment.column_extract_code is None or experiment.column_extract_code == '':
        form.column_extract_code.data = """def parse(run_output)\n    csv_string = '' #'key1=val1,key2=val2...'\n    return csv_string"""
    else:
        form.column_extract_code.data = experiment.column_extract_code
    return render_template("experiment_settings.html", title='Settings', form=form
                           , experiments=experiments
                           , add_experiment_form=add_experiment_form
                           , experiment_id=int(experiment_id)
                           ,experiment=experiment)

    
