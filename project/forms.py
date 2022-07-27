import email
from wsgiref.validate import validator
from xmlrpc.client import DateTime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, DateField, IntegerField, RadioField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from project.models import User
from datetime import date, datetime

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username Already Taken!')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('E-mail Already Registered!')

class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpeg','png','jpg'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username Already Taken!')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('E-mail Already Registered!')
    
class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content =  TextAreaField('Content', validators=[DataRequired()])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d')
    contact = IntegerField('Contact', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    type = RadioField('Post Type', choices=[(1,'Donate'), (2,'Request')], default=1, coerce=int)
    pic = FileField('Image', validators=[FileAllowed(['jpeg','png','jpg'])])

    submit = SubmitField('Post')

    def validate_contact(self, contact):
        num = len(str(contact.data))
        if num!=10 :
            raise ValidationError('Contact Number should be 10 digits')

    def validate_expiry_date(form, expiry_date):
        if expiry_date.data:
            if expiry_date.data < date.today():
                raise ValidationError("The date cannot be in the past!")

class SearchForm(FlaskForm):
    item = StringField('item', validators=[DataRequired()])
    types = SelectField('types', choices=[('3', 'All'), ('1', 'Donation'), ('2', 'Request')], default='3')
    submit = SubmitField('submit')

class RequestResetForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('E-mail Does not Exist')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset')

class ConnectForm(FlaskForm):
    notify = SubmitField('Notify')