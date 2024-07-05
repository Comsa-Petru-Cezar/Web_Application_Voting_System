import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, ValidationError, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from Application.models import User, Election, Candidate
from flask_login import current_user


class RegForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2,max=20)])
    email = StringField('Email',  validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('email already in use')


class LogForm(FlaskForm):
    email = StringField('Email',  validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')


class UpdateAccForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',  validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already exists')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('email already in use')


class CandidateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    votes = 0
    submit = SubmitField('Post')
    def manually_validate_name(self, name, election):
        if name.data in [x.name for x in Candidate.query.filter_by(election_id=election).all()]:
            return False
        return True


class ElectionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Post')

    def validate_title(self, title):
        user = Election.query.filter_by(title=title.data).first()
        if user:
            raise ValidationError('Election name already in use')

    def validate_start_date(self, start_date):
        if start_date.data < datetime.date.today():
            raise ValidationError('End Date must be after Start Date')

    def validate_end_date(self, end_date):
        if end_date.data < self.start_date.data:
            raise ValidationError('End Date must be after Start Date')

