from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from myproject.models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationFrom(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('pass_confirm',
                                                                             message='Passwords must match!')])
    pass_confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def check_email(self, field):
        if User.query.filter_by(email=self.email.data).first():
            raise ValidationError('Your Email has been already Registered!')

    def check_username(self, field):
        if User.query.filter_by(username=self.username.data).first():
            raise ValidationError('Username already exists!')


class UpdateUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    profile_image = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    user_bio = StringField('Bio')
    submit = SubmitField('Update')

    def check_email(self, field):
        # Check if not None for that user email!
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Your email has been registered already!')

    def check_username(self, field):
        # Check if not None for that username!
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Sorry, that username is taken!')


class ReviewsForm(FlaskForm):
    review_text = TextAreaField('Write Review', validators=[DataRequired()])
    submit = SubmitField('Post')

