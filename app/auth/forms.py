from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
class LoginForm(FlaskForm):
    email=StringField('Email', validators=[DataRequired(), Email()]); password=PasswordField('Password', validators=[DataRequired()]); remember=BooleanField('Remember me'); submit=SubmitField('Login')
class RegisterForm(FlaskForm):
    email=StringField('Email', validators=[DataRequired(), Email()]); password=PasswordField('Password', validators=[DataRequired(), Length(min=8)]); confirm_password=PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')]); role=SelectField('Account type', choices=[('candidate','Job Seeker'),('recruiter','Recruiter')]); submit=SubmitField('Create account')
class ForgotPasswordForm(FlaskForm):
    email=StringField('Email', validators=[DataRequired(), Email()]); submit=SubmitField('Send reset link')
class ResetPasswordForm(FlaskForm):
    password=PasswordField('New password', validators=[DataRequired(), Length(min=8)]); confirm_password=PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')]); submit=SubmitField('Reset password')
