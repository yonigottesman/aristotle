from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, FieldList
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User


class AddRunForm(FlaskForm):
    columns = StringField('Columns - CSV String', validators=[])
    description = StringField('Description', validators=[DataRequired()])
    run_result = TextAreaField('Run Output', validators=[ DataRequired()])
    submit = SubmitField('Add')

    
class EditRunForm(FlaskForm):
    columns = StringField('Columns - CSV String', validators=[])
    description = StringField('Description', validators=[])
    run_result = TextAreaField('Run Output', validators=[])
    delete = BooleanField('Delete Run')
    submit = SubmitField('Update')    

    
class AddExperimentForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Add')    

    
class EditExperimentForm(FlaskForm):
    description = StringField('Description', validators=[])
    columns = StringField('Columns - CSV String', validators=[])
    delete = BooleanField('Delete Experiment')
    column_extract_code = TextAreaField('Parse run output code to colunms', validators=[])
    submit = SubmitField('Update')    


