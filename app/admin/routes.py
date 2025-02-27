from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from ..models.database import db, Admin, Note, Major, Semester, Lesson, Teacher, User, Subscription
from .forms import LoginForm, NoteUploadForm
import os
from datetime import datetime
# import jdatetime
from config import Config
import asyncio
from telegram import Bot
import nest_asyncio
from . import bp
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

def convert_persian_date(date_str):
    """Convert Persian date string to Gregorian datetime object."""
    if not date_str or not date_str.strip():
        return datetime.now().date()  # Return today's date as default
    try:
        # Parse the date string in YYYY/MM/DD format
        year, month, day = map(int, date_str.strip().split('/'))
        return datetime(year, month, day).date()
    except Exception as e:
        print(f"Error converting date: {e}")
        return datetime.now().date()  # Return today's date as fallback

def sync_notify_subscribers(bot_token, note, lesson):
    """Synchronous wrapper for notification function."""
    try:
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_notifications():
            bot = Bot(token=bot_token)
            # Get bot info first to ensure connection
            bot_info = await bot.get_me()
            
            subscribers = User.query.join(Subscription).filter(
                Subscription.lesson_id == lesson.id
            ).all()
            
            if not subscribers:
                print("هیچ مشترکی برای این درس یافت نشد")
                return
                
            notification_text = (
                f"📢 جزوه جدید!\n\n"
                f"*{note.name}*\n"
                f"درس: {lesson.name}\n"
                f"استاد: {note.teacher.name}\n"
                f"نویسنده: {note.author}\n\n"
                f"[📥 دانلود جزوه](https://t.me/{bot_info.username}?start=note_{note.id})"
            )
            
            for subscriber in subscribers:
                try:
                    await bot.send_message(
                        chat_id=subscriber.telegram_id,
                        text=notification_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    print(f"اعلان برای کاربر {subscriber.telegram_id} ارسال شد")
                except Exception as e:
                    print(f"خطا در ارسال اعلان به کاربر {subscriber.telegram_id}: {e}")
        
        # Run the async function in the new event loop
        loop.run_until_complete(send_notifications())
    except Exception as e:
        print(f"خطا در تابع sync_notify_subscribers: {e}")
    finally:
        try:
            loop.close()
        except:
            pass

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    return redirect(url_for('admin.dashboard'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            flash('با موفقیت وارد شدید.', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('نام کاربری یا رمز عبور نامعتبر است.', 'danger')
    return render_template('admin/login.html', form=form)

@bp.route('/dashboard')
@login_required
def dashboard():
    notes = Note.query.order_by(Note.upload_date.desc()).all()
    return render_template('admin/dashboard.html', notes=notes)

@bp.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    form = NoteUploadForm()
    
    if request.method == 'GET':
        # Pre-fill form with existing note data
        form.name.data = note.name
        form.author.data = note.author
        # Format date as YYYY/MM/DD
        if note.date_written:
            form.date_written.data = note.date_written.strftime("%Y/%m/%d")
        form.description.data = note.description
        form.major.data = note.teacher.lesson.semester.major.name
        form.semester.data = note.teacher.lesson.semester.name
        form.lesson.data = note.teacher.lesson.name
        form.teacher.data = note.teacher.name
    
    if form.validate_on_submit():
        try:
            # Update note details
            note.name = form.name.data
            note.author = form.author.data
            note.date_written = convert_persian_date(form.date_written.data)
            note.description = form.description.data
            
            # Handle file upload if new file is provided
            if form.file.data:
                # Delete old file
                if os.path.exists(note.file_path):
                    os.remove(note.file_path)
                
                # Save new file
                file = form.file.data
                filename = secure_filename(file.filename)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                note.file_path = file_path
            
            # Update or create major, semester, lesson, and teacher
            major = Major.query.filter_by(name=form.major.data).first()
            if not major:
                major = Major(name=form.major.data)
                db.session.add(major)
                db.session.flush()
            
            semester = Semester.query.filter_by(name=form.semester.data, major_id=major.id).first()
            if not semester:
                semester = Semester(name=form.semester.data, major_id=major.id)
                db.session.add(semester)
                db.session.flush()
            
            lesson = Lesson.query.filter_by(name=form.lesson.data, semester_id=semester.id).first()
            if not lesson:
                lesson = Lesson(name=form.lesson.data, semester_id=semester.id)
                db.session.add(lesson)
                db.session.flush()
            
            teacher = Teacher.query.filter_by(name=form.teacher.data, lesson_id=lesson.id).first()
            if not teacher:
                teacher = Teacher(name=form.teacher.data, lesson_id=lesson.id)
                db.session.add(teacher)
                db.session.flush()
            
            note.teacher_id = teacher.id
            db.session.commit()
            
            flash('جزوه با موفقیت به‌روزرسانی شد!', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در به‌روزرسانی جزوه: {str(e)}', 'danger')
    
    return render_template('admin/upload_note.html', form=form, edit_mode=True)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_note():
    form = NoteUploadForm()
    
    if form.validate_on_submit():
        try:
            # Create upload directory if it doesn't exist
            if not os.path.exists(Config.UPLOAD_FOLDER):
                os.makedirs(Config.UPLOAD_FOLDER)

            # Handle file upload
            file = form.file.data
            if not file:
                flash('فایل برای جزوه‌های جدید الزامی است.', 'danger')
                return render_template('admin/upload_note.html', form=form, edit_mode=False)
                
            filename = secure_filename(file.filename)
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            
            # Create or get major
            major = Major.query.filter_by(name=form.major.data).first()
            if not major:
                major = Major(name=form.major.data)
                db.session.add(major)
                db.session.flush()
            
            # Create or get semester
            semester = Semester.query.filter_by(name=form.semester.data, major_id=major.id).first()
            if not semester:
                semester = Semester(name=form.semester.data, major_id=major.id)
                db.session.add(semester)
                db.session.flush()
            
            # Create or get lesson
            lesson = Lesson.query.filter_by(name=form.lesson.data, semester_id=semester.id).first()
            if not lesson:
                lesson = Lesson(name=form.lesson.data, semester_id=semester.id)
                db.session.add(lesson)
                db.session.flush()
            
            # Create or get teacher
            teacher = Teacher.query.filter_by(name=form.teacher.data, lesson_id=lesson.id).first()
            if not teacher:
                teacher = Teacher(name=form.teacher.data, lesson_id=lesson.id)
                db.session.add(teacher)
                db.session.flush()
        
            # Save file
            file.save(file_path)
            
            # Create note
            note = Note(
                name=form.name.data,
                author=form.author.data,
                date_written=convert_persian_date(form.date_written.data),
                description=form.description.data,
                file_path=file_path,
                teacher_id=teacher.id,
                upload_date=datetime.utcnow(),
                rating_sum=0,
                rating_count=0
            )
            
            db.session.add(note)
            db.session.commit()
            
            # Notify subscribers
            bot_token = Config.TELEGRAM_TOKEN
            if bot_token:
                try:
                    sync_notify_subscribers(bot_token, note, lesson)
                    print("فرآیند اعلان‌رسانی تکمیل شد")
                except Exception as e:
                    print(f"خطا در اعلان‌رسانی: {e}")
            
            flash('جزوه با موفقیت آپلود شد!', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در آپلود جزوه: {str(e)}', 'danger')

    return render_template('admin/upload_note.html', form=form, edit_mode=False)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('با موفقیت خارج شدید.', 'success')
    return redirect(url_for('admin.login'))

@bp.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    try:
        # Delete file
        if os.path.exists(note.file_path):
            os.remove(note.file_path)
        
        # Delete note from database
        db.session.delete(note)
        db.session.commit()
        flash('جزوه با موفقیت حذف شد!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا در حذف جزوه: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@bp.route('/users')
@login_required
def users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template('admin/users.html', users=users)

@bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        user_ids = request.form.getlist('user_ids[]')
        message = request.form.get('message')
        
        if not message:
            return jsonify({'success': False, 'error': 'پیام نمی‌تواند خالی باشد.'})
        
        bot_token = Config.TELEGRAM_TOKEN
        if not bot_token:
            return jsonify({'success': False, 'error': 'توکن تلگرام یافت نشد.'})

        # Create new event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def send_messages():
            bot = Bot(token=bot_token)
            success_count = 0
            failed_count = 0
            
            for user_id in user_ids:
                user = User.query.get(user_id)
                if user and user.telegram_id:
                    try:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=message,
                            parse_mode='Markdown'
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error sending message to user {user.telegram_id}: {e}")
                        failed_count += 1
            
            return success_count, failed_count

        # Run the async function
        success_count, failed_count = loop.run_until_complete(send_messages())
        loop.close()
        
        return jsonify({
            'success': True,
            'message': f'پیام با موفقیت به {success_count} کاربر ارسال شد. {failed_count} ارسال ناموفق.'
        })
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        return jsonify({'success': False, 'error': str(e)}) 