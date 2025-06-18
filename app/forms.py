from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired
from datetime import date

# Custom validator to ensure the provided date is not in the future.
def date_is_not_in_future(form, field):
    """
    Custom validator to ensure the provided date is not in the future.
    """
    if field.data and field.data > date.today():
        raise ValidationError('Date of birth cannot be in the future.')

class LoginForm(FlaskForm):
    email    = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    email            = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password         = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[
                           DataRequired(), EqualTo('password', message='Passwords must match')])
    # The 'role' field is intentionally removed for security.

class PatientCheckForm(FlaskForm):
    name            = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    date_of_birth   = DateField('Date of Birth', format='%Y-%m-%d', validators=[
                                  DataRequired(), 
                                  date_is_not_in_future # Future-date validator is included
                                ])
    medical_history = TextAreaField('Medical History', validators=[Length(max=2000)])
    symptoms        = TextAreaField('Current Symptoms', validators=[Length(max=2000)])
    image           = FileField('Retina Image', validators=[
                          FileRequired(), FileAllowed(['jpg','jpeg','png'], 'Only JPG/PNG allowed')])