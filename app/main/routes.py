from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Run, Experiment, FileContent
from app.main.forms import AddRunForm, AddExperimentForm, EditExperimentForm, EditRunForm
from app import db, images
from werkzeug.urls import url_parse
from RestrictedPython import compile_restricted
from AccessControl.ZopeGuards import get_safe_globals
from app.main import bp
from flask import current_app as app
from werkzeug.utils import secure_filename
import os

@login_required
@bp.route('/experiment/<experiment_id>/compare', methods=['GET', 'POST'])
def compare(experiment_id):
    run1_id = request.args.get('run1')
    run2_id = request.args.get('run2')
    run1 = Run.query.filter_by(id=run1_id, user_id=current_user.id).first_or_404()
    run2 = Run.query.filter_by(id=run2_id, user_id=current_user.id).first_or_404()

    run1_images = run1.files.all()
    run2_images = run2.files.all()
    
    t = create_experiment_table([run1, run2])
    table = t[1:]
    columns = t[0]
    
    return render_template("compare.html", run1=run1,run2=run2
                           , columns=columns
                           , table=table
                           , run1_images=run1_images
                           , run2_images=run2_images
                           , column_range=range(len(columns)))


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


def render_run(run, form):
    
    add_experiment_form = AddExperimentForm()
    experiments = current_user.experiments.all()
    run_images = run.files.all()
    return render_template("run.html", title='Run'
                           , add_experiment_form=add_experiment_form
                           , experiments=experiments
                           , add_run_form=form
                           , run=run
                           , images=run_images)    
    
    
@login_required
@bp.route('/experiment/<experiment_id>/run/<run_id>', methods=['GET', 'POST'])
def run(experiment_id,run_id):
    run = Run.query.filter_by(id=run_id, user_id=current_user.id).first_or_404()
    experiment = Experiment.query.filter_by(id=experiment_id).first_or_404()
    
    form = EditRunForm()

    if form.validate_on_submit():
        if form.delete.data == True:
            db.session.delete(run)
            db.session.commit()
            return redirect(url_for('main.experiment', experiment_id=experiment_id))
        else:
            
            columns = ''
            if experiment.column_extract_code is not None and form.run_result.data != '':
                # extract columns from output
                # TODO This part should be done once when code is submitted.
                source_code = experiment.column_extract_code
                try:
                    byte_code = compile_restricted(source_code, filename='<inline code>', mode='exec')
                    loc = {}
                    exec(byte_code,get_safe_globals(),loc)
                
                    columns = loc['parse'](form.run_result.data)
                    if columns is None:
                        columns = ''
            
                    if validat_csv(columns) == False:
                        form.run_result.errors.append('exctracted columns wrongs format: ' + columns)
                        return render_experiment(experiment, form)
            
                except Exception as e:
                    form.run_result.errors.append('Error while parsing:' + str(e))
                    return render_run(run, form)
            
                columns = clean_columns(columns)
                run.result_inffered_columns = columns
                
            if form.run_result.data != '':
                run.run_result = form.run_result.data
                
            if validat_csv(form.columns.data) == False:
                form.columns.errors.append('columns wrongs format')
                return render_run(run, form)

            if clean_columns(form.columns.data) != '':
                run.columns = clean_columns(form.columns.data)

            if form.description.data != '':
                run.description = form.description.data
                
            if form.upload_file.data is not None:
                f = form.upload_file.data
                fn = images.save(f,run_id)
                new_file = FileContent(run_id=run.id, file_name=fn)
                db.session.add(new_file)

            db.session.add(run)
            db.session.commit()
            return redirect(url_for('main.run', experiment_id=experiment_id, run_id=run_id))
        
    return render_run(run, form)


def validat_csv(line):
    if line is None:
        return True
    for i in line.split(','):
        if i.strip() != '':
            if len(i.split('=')) != 2:
                return False
    return True


def create_experiment_table(runs):
    column_names = []
    run_columns_dict = {}

    for run in runs:
        
        columns_raw = run.columns.split(',') + run.result_inffered_columns.split(',')
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
        table.append({'run':run, 'columns':list(defaults.values())})

    return [column_names] + table


def clean_columns(columns_csv):
    cleaned = []
    for column in columns_csv.split(','):
        if column.strip() != '':
            key = column.split('=')[0].strip()
            value = column.split('=')[1].strip()
            cleaned.append(key+'='+value)
    return ', '.join(cleaned)


def render_experiment(experiment, add_run_form):
    experiments = current_user.experiments.all()
    runs = current_user.runs.filter(Run.experiment_id==experiment.id)
    t = create_experiment_table(runs)
    table = t[1:]
    columns = t[0]
    add_run_form.columns.data = runs[-1].columns+','
    add_experiment_form = AddExperimentForm()

    return render_template("experiment.html", title='Experiment', add_run_form=add_run_form
                           , add_experiment_form=add_experiment_form
                           , experiments=experiments
                           , experiment_id=experiment.id
                           , columns=columns
                           , table=table
                           , column_range=range(len(columns)))
    

@login_required
@bp.route('/experiment/<experiment_id>', methods=['GET', 'POST'])
def experiment(experiment_id):
    experiment = Experiment.query.filter_by(id=experiment_id).first_or_404()
    form = AddRunForm()

    if form.validate_on_submit():
        columns = ''
        if experiment.column_extract_code is not None:
            # extract columns from output
            # TODO This part should be done once when code is submitted.
            source_code = experiment.column_extract_code
            try:
                byte_code = compile_restricted(source_code, filename='<inline code>', mode='exec')
                loc = {}
                exec(byte_code,get_safe_globals(),loc)
                
                columns = loc['parse'](form.run_result.data)
                if columns is None:
                    columns = ''
            
                if validat_csv(columns) == False:
                    form.run_result.errors.append('exctracted columns wrongs format: ' + columns)
                    return render_experiment(experiment, form)
            
            except Exception as e:
                form.run_result.errors.append('Error while parsing:' + str(e))
                return render_experiment(experiment, form)
            
            columns = clean_columns(columns)
            
        if validat_csv(form.columns.data) == False:
            form.columns.errors.append('columns wrongs format')
            return render_experiment(experiment, form)

        
        # if columns == '':
        #     columns = clean_columns(form.columns.data)
        # else:
        #     columns = columns + ', ' + clean_columns(form.columns.data)

        run = Run(description=form.description.data
                  , run_result=form.run_result.data, owner=current_user
                  , result_inffered_columns=columns
                  , columns = clean_columns(form.columns.data)
                  , experiment_id=int(experiment_id))
        db.session.add(run)
        db.session.commit()
        
        if form.upload_file.data is not None:
            f = form.upload_file.data
            fn = images.save(f,str(run.id))
            new_file = FileContent(run_id=run.id, file_name=fn)
            db.session.add(new_file)
            db.session.commit()

        return redirect(url_for('main.experiment',experiment_id=experiment_id))
    
    return render_experiment(experiment, form)

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


def render_settings(experiment, form, compilation_error=None):
    experiments = current_user.experiments.all()
    add_experiment_form = AddExperimentForm()
    if experiment.column_extract_code is None or experiment.column_extract_code == '':
        form.column_extract_code.data = """def parse(run_output):\n    csv_string = '' #'key1=val1,key2=val2...'\n    return csv_string"""
    else:
        form.column_extract_code.data = experiment.column_extract_code
    return render_template("experiment_settings.html", title='Settings', form=form
                           , experiments=experiments
                           , add_experiment_form=add_experiment_form
                           , experiment_id=experiment.id
                           , experiment=experiment
                           , compilation_error=compilation_error)
    


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
                try:
                    byte_code = compile_restricted(experiment.column_extract_code, filename='<inline code>', mode='exec')
                    loc = {}
                    exec(byte_code,get_safe_globals(),loc)
                except SyntaxError as e:
                    return render_settings(experiment, form, e)

            db.session.add(experiment)
            db.session.commit()
            return redirect(url_for('main.experiment', experiment_id=experiment_id))        

    return render_settings(experiment, form)
    
