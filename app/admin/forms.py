from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(message='نام کاربری الزامی است')])
    password = PasswordField('رمز عبور', validators=[DataRequired(message='رمز عبور الزامی است')])
    submit = SubmitField('ورود')

class NoteUploadForm(FlaskForm):
    name = StringField('نام جزوه', validators=[DataRequired(message='نام جزوه الزامی است')])
    author = StringField('نویسنده', validators=[DataRequired(message='نام نویسنده الزامی است')])
    date_written = StringField('تاریخ نگارش', validators=[DataRequired(message='تاریخ نگارش الزامی است')])
    description = TextAreaField('توضیحات')
    major = StringField('رشته', validators=[DataRequired(message='نام رشته الزامی است')])
    semester = StringField('نیمسال', validators=[DataRequired(message='نام نیمسال الزامی است')])
    lesson = StringField('درس', validators=[DataRequired(message='نام درس الزامی است')])
    teacher = StringField('استاد', validators=[DataRequired(message='نام استاد الزامی است')])
    file = FileField('فایل جزوه', validators=[
        FileAllowed(['pdf'], 'فقط فایل‌های PDF مجاز هستند')
    ])
    submit = SubmitField('ذخیره') 