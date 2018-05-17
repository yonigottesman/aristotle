from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, FieldList
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User
from app import images
from flask_wtf.file import FileField, FileAllowed, FileRequired



class AddRunForm(FlaskForm):
    columns = StringField('Columns - CSV String', validators=[])
    description = StringField('Description', validators=[])
    run_result = TextAreaField('Run Output', validators=[])
    upload_file = FileField('upload_file', validators=[FileAllowed(images, 'Images only!') ])
    submit = SubmitField('Add')

    
class EditRunForm(FlaskForm):
    columns = StringField('Columns - CSV String', validators=[])
    description = StringField('Description', validators=[])
    run_result = TextAreaField('Run Output', validators=[])
    delete = BooleanField('Delete Run')
    upload_file = FileField('upload_file', validators=[FileAllowed(images, 'Images only!') ])
    submit = SubmitField('Update')    

    
class AddExperimentForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Add')    

    
class EditExperimentForm(FlaskForm):
    description = StringField('Description', validators=[])
    column_ignore_list = StringField('Hidden Column list', validators=[])
    delete = BooleanField('Delete Experiment')
    column_extract_code = TextAreaField('Parse run output code to colunms', validators=[])
    submit = SubmitField('Update')    


