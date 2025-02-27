import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from app.models.database import db, Major, Semester, Lesson, Teacher, Note, Subscription, User

# Define conversation states
CHOOSING, MAJOR, SEMESTER, LESSON, TEACHER, NOTES, RATING = range(7)

logger = logging.getLogger(__name__)

def format_date(date):
    """Format date as string."""
    if not date:
        return ""
    return date.strftime("%Y/%m/%d")

class TelegramBotHandlers:
    def __init__(self, app):
        self.app = app

    def get_handlers(self):
        """Return the conversation handler with all states and callbacks."""
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', self.start),
                CallbackQueryHandler(self.start, pattern='^start$')
            ],
            states={
                CHOOSING: [
                    CallbackQueryHandler(self.browse_notes, pattern='^browse$'),
                    CallbackQueryHandler(self.about, pattern='^about$'),
                    CallbackQueryHandler(self.start, pattern='^back$'),
                ],
                MAJOR: [
                    CallbackQueryHandler(self.handle_major, pattern='^(major_|back$)'),
                ],
                SEMESTER: [
                    CallbackQueryHandler(self.handle_semester, pattern='^(semester_|back$)'),
                ],
                LESSON: [
                    CallbackQueryHandler(self.handle_subscription, pattern='^(subscribe_|unsubscribe_)'),
                    CallbackQueryHandler(self.handle_lesson, pattern='^(lesson_|back$)'),
                ],
                TEACHER: [
                    CallbackQueryHandler(self.handle_subscription, pattern='^(subscribe_|unsubscribe_)'),
                    CallbackQueryHandler(self.handle_teacher, pattern='^(teacher_|back$)'),
                ],
                RATING: [
                    CallbackQueryHandler(self.handle_rating, pattern='^(rate_|back$)'),
                    CallbackQueryHandler(self.start, pattern='^start$'),
                ]
            },
            fallbacks=[
                CommandHandler('start', self.start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.start)
            ],
            per_message=False
        )
        return [conv_handler]

    async def start(self, update: Update, context: CallbackContext) -> int:
        """Start the conversation and display the main menu."""
        try:
            with self.app.app_context():
                # Create or update user
                user = User.query.filter_by(telegram_id=update.effective_user.id).first()
                if not user:
                    user = User(
                        telegram_id=update.effective_user.id,
                        username=update.effective_user.username,
                        join_date=datetime.utcnow(),
                        is_blocked=False,
                        last_active=datetime.utcnow()
                    )
                    db.session.add(user)
                else:
                    user.last_active = datetime.utcnow()
                    if user.username != update.effective_user.username:
                        user.username = update.effective_user.username
                db.session.commit()

                # Check if user is blocked
                if user.is_blocked:
                    if update.message:
                        await update.message.reply_text(
                            "⛔️ شما از استفاده از ربات محدود شده‌اید. لطفاً با مدیر تماس بگیرید."
                        )
                    return ConversationHandler.END

                # Handle note_id from deep linking
                if context.args and context.args[0].startswith('note_'):
                    try:
                        note_id = int(context.args[0].split('_')[1])
                        return await self.send_note(update, context, note_id)
                    except (ValueError, IndexError):
                        logger.error("Invalid note_id in deep link")
                
                keyboard = [
                    [InlineKeyboardButton("📚 مرور جزوه‌ها", callback_data='browse')],
                    [InlineKeyboardButton("ℹ️ درباره ربات", callback_data='about')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                text = (
                    "🎓 به ربات جزوه‌های دانشگاهی خوش آمدید!\n\n"
                    "این ربات به شما کمک می‌کند تا جزوه‌های درسی را پیدا و به اشتراک بگذارید.\n\n"
                    "چه کاری می‌خواهید انجام دهید؟"
                )
                
                if update.callback_query:
                    await update.callback_query.answer()
                    await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
                else:
                    await update.message.reply_text(text, reply_markup=reply_markup)
                
                return CHOOSING

        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            try:
                if update.callback_query:
                    await update.callback_query.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
                elif update.message:
                    await update.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")
            except Exception as inner_e:
                logger.error(f"Error sending error message: {inner_e}")
            return CHOOSING

    async def browse_notes(self, update: Update, context: CallbackContext) -> int:
        """Show available majors."""
        query = update.callback_query
        await query.answer()

        with self.app.app_context():
            majors = Major.query.all()
            keyboard = [
                [InlineKeyboardButton(major.name, callback_data=f'major_{major.id}')]
                for major in majors
            ]
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                "لطفاً رشته تحصیلی خود را انتخاب کنید:",
                reply_markup=reply_markup
            )
            return MAJOR

    async def handle_major(self, update: Update, context: CallbackContext) -> int:
        """Handle major selection and show semesters."""
        query = update.callback_query
        await query.answer()

        if query.data == 'back':
            return await self.start(update, context)

        major_id = int(query.data.split('_')[1])
        context.user_data['major_id'] = major_id

        with self.app.app_context():
            semesters = Semester.query.filter_by(major_id=major_id).all()
            major = Major.query.get(major_id)
            keyboard = [
                [InlineKeyboardButton(semester.name, callback_data=f'semester_{semester.id}')]
                for semester in semesters
            ]
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                f"نیمسال‌های {major.name}:\n"
                "لطفاً نیمسال را انتخاب کنید:",
                reply_markup=reply_markup
            )
            return SEMESTER

    async def handle_semester(self, update: Update, context: CallbackContext) -> int:
        """Handle semester selection and show lessons."""
        query = update.callback_query
        await query.answer()

        if query.data == 'back':
            return await self.browse_notes(update, context)

        semester_id = int(query.data.split('_')[1])
        context.user_data['semester_id'] = semester_id

        with self.app.app_context():
            lessons = Lesson.query.filter_by(semester_id=semester_id).all()
            semester = Semester.query.get(semester_id)
            keyboard = [
                [InlineKeyboardButton(lesson.name, callback_data=f'lesson_{lesson.id}')]
                for lesson in lessons
            ]
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                f"درس‌های {semester.name}:\n"
                "لطفاً درس مورد نظر را انتخاب کنید:",
                reply_markup=reply_markup
            )
            return LESSON

    async def handle_lesson(self, update: Update, context: CallbackContext) -> int:
        """Handle lesson selection and show teachers."""
        query = update.callback_query
        await query.answer()

        if query.data == 'back':
            semester_id = context.user_data.get('semester_id')
            if semester_id:
                return await self.handle_semester(update, context)
            return await self.browse_notes(update, context)

        lesson_id = int(query.data.split('_')[1])
        context.user_data['lesson_id'] = lesson_id

        with self.app.app_context():
            teachers = Teacher.query.filter_by(lesson_id=lesson_id).all()
            lesson = Lesson.query.get(lesson_id)
            
            user = User.query.filter_by(telegram_id=query.from_user.id).first()
            if not user:
                user = User(telegram_id=query.from_user.id, username=query.from_user.username)
                db.session.add(user)
                db.session.commit()
            
            is_subscribed = Subscription.query.filter_by(
                user_id=user.id,
                lesson_id=lesson_id
            ).first() is not None

            keyboard = [
                [InlineKeyboardButton(teacher.name, callback_data=f'teacher_{teacher.id}')]
                for teacher in teachers
            ]
            
            sub_button = InlineKeyboardButton(
                "🔕 لغو اشتراک" if is_subscribed else "🔔 دریافت اعلان",
                callback_data=f'{"unsubscribe" if is_subscribed else "subscribe"}_{lesson_id}'
            )
            keyboard.append([sub_button])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                f"اساتید درس {lesson.name}:\n"
                "لطفاً استاد مورد نظر را انتخاب کنید:",
                reply_markup=reply_markup
            )
            return TEACHER

    async def handle_teacher(self, update: Update, context: CallbackContext) -> int:
        """Handle teacher selection and show notes."""
        query = update.callback_query
        await query.answer()

        if query.data == 'back':
            lesson_id = context.user_data.get('lesson_id')
            if lesson_id:
                return await self.handle_lesson(update, context)
            return await self.browse_notes(update, context)

        teacher_id = int(query.data.split('_')[1])
        context.user_data['teacher_id'] = teacher_id

        with self.app.app_context():
            teacher = Teacher.query.get(teacher_id)
            notes = Note.query.filter_by(teacher_id=teacher_id).all()
            
            if not notes:
                keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text(
                    f"هیچ جزوه‌ای برای {teacher.name} یافت نشد.",
                    reply_markup=reply_markup
                )
                return TEACHER

            overview = f"جزوه‌های درس {teacher.lesson.name} استاد {teacher.name}:\n\n"
            keyboard = []
            
            for note in notes:
                overview += (
                    f"📝 *{note.name}*\n"
                    f"نویسنده: {note.author}\n"
                    f"تاریخ: {format_date(note.date_written)}\n"
                    f"امتیاز: {note.average_rating:.1f}⭐ ({note.rating_count} رأی)\n"
                    f"[📥 دانلود جزوه](https://t.me/{context.bot.username}?start=note_{note.id})\n\n"
                )

            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                overview,
                reply_markup=reply_markup,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            return TEACHER

    async def handle_rating(self, update: Update, context: CallbackContext) -> int:
        """Handle rating submission."""
        query = update.callback_query
        await query.answer()

        if query.data == 'back':
            return await self.start(update, context)

        try:
            rating_data = query.data.split('_')
            if len(rating_data) == 3 and rating_data[0] == 'rate':
                note_id = int(rating_data[1])
                rating = int(rating_data[2])

                with self.app.app_context():
                    note = Note.query.get(note_id)
                    if note:
                        note.rating_sum = (note.rating_sum or 0) + rating
                        note.rating_count = (note.rating_count or 0) + 1
                        db.session.commit()

                        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back')]]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        await query.message.edit_text(
                            f"با تشکر از امتیاز شما! شما به این جزوه {rating}⭐ دادید.\n"
                            f"میانگین امتیاز اکنون {note.average_rating:.1f}⭐ است.\n\n"
                            "برای بازگشت به منوی اصلی روی دکمه زیر کلیک کنید.",
                            reply_markup=reply_markup
                        )
                        return RATING

            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                "خطا در ثبت امتیاز. لطفاً دوباره تلاش کنید.\n\n"
                "برای بازگشت به منوی اصلی روی دکمه زیر کلیک کنید.",
                reply_markup=reply_markup
            )
            return RATING

        except Exception as e:
            logger.error(f"Error handling rating: {e}")
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                "خطا در ثبت امتیاز. لطفاً دوباره تلاش کنید.\n\n"
                "برای بازگشت به منوی اصلی روی دکمه زیر کلیک کنید.",
                reply_markup=reply_markup
            )
            return RATING

    async def handle_subscription(self, update: Update, context: CallbackContext) -> int:
        """Handle subscription/unsubscription to lessons."""
        query = update.callback_query
        await query.answer()

        action, lesson_id = query.data.split('_')
        lesson_id = int(lesson_id)
        context.user_data['lesson_id'] = lesson_id

        with self.app.app_context():
            user = User.query.filter_by(telegram_id=query.from_user.id).first()
            if not user:
                user = User(telegram_id=query.from_user.id, username=query.from_user.username)
                db.session.add(user)
                db.session.commit()

            lesson = Lesson.query.get(lesson_id)
            if not lesson:
                await query.message.edit_text("درس مورد نظر یافت نشد.")
                return CHOOSING

            existing_sub = Subscription.query.filter_by(
                user_id=user.id,
                lesson_id=lesson_id
            ).first()

            message = ""
            if action == 'subscribe' and not existing_sub:
                subscription = Subscription(user_id=user.id, lesson_id=lesson_id)
                db.session.add(subscription)
                db.session.commit()
                message = "✅ شما با موفقیت مشترک دریافت اعلان‌های جزوه‌های جدید شدید!"
            elif action == 'unsubscribe' and existing_sub:
                db.session.delete(existing_sub)
                db.session.commit()
                message = "✅ اشتراک شما با موفقیت لغو شد."

            teachers = Teacher.query.filter_by(lesson_id=lesson_id).all()
            is_subscribed = Subscription.query.filter_by(
                user_id=user.id,
                lesson_id=lesson_id
            ).first() is not None

            keyboard = [
                [InlineKeyboardButton(teacher.name, callback_data=f'teacher_{teacher.id}')]
                for teacher in teachers
            ]
            sub_button = InlineKeyboardButton(
                "🔕 لغو اشتراک" if is_subscribed else "🔔 دریافت اعلان",
                callback_data=f'{"unsubscribe" if is_subscribed else "subscribe"}_{lesson_id}'
            )
            keyboard.append([sub_button])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(keyboard)

            text = f"اساتید درس {lesson.name}:\n"
            if message:
                text += f"\n{message}\n\n"
            text += "لطفاً استاد مورد نظر را انتخاب کنید:"
            
            await query.message.edit_text(text, reply_markup=reply_markup)
            return TEACHER

    async def send_note(self, update: Update, context: CallbackContext, note_id: int) -> int:
        """Send a note to the user."""
        with self.app.app_context():
            try:
                if update.callback_query:
                    chat_id = update.callback_query.message.chat_id
                    await update.callback_query.answer()
                else:
                    chat_id = update.message.chat_id

                note = Note.query.get(note_id)
                if note and os.path.exists(note.file_path):
                    try:
                        with open(note.file_path, 'rb') as file:
                            sent_file = await context.bot.send_document(
                                chat_id=chat_id,
                                document=file,
                                read_timeout=60,
                                write_timeout=60
                            )
                        
                        keyboard = []
                        rating_buttons = []
                        for i in range(1, 6):
                            rating_buttons.append(
                                InlineKeyboardButton(f"{i}⭐", callback_data=f'rate_{note_id}_{i}')
                            )
                        keyboard.append(rating_buttons)
                        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back')])
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        description_text = f"📋 توضیحات:\n{note.description}\n\n" if note.description else ""
                        info_text = (
                            f"*{note.name}*\n"
                            f"👨‍🏫 استاد: {note.teacher.name}\n"
                            f"📚 رشته: {note.teacher.lesson.semester.major.name}\n"
                            f"📅 نیمسال: {note.teacher.lesson.semester.name}\n"
                            f"📖 درس: {note.teacher.lesson.name}\n"
                            f"✍️ نویسنده: {note.author}\n"
                            f"📅 تاریخ نگارش: {format_date(note.date_written)}\n"
                            f"{description_text}"
                            f"⭐ امتیاز: {note.average_rating:.1f} ({note.rating_count} رأی)\n\n"
                            f"لطفاً به این جزوه امتیاز دهید:"
                        )
                        
                        await sent_file.reply_text(
                            text=info_text,
                            reply_markup=reply_markup,
                            parse_mode='Markdown'
                        )
                        return RATING
                        
                    except Exception as e:
                        logger.error(f"Error sending note: {e}")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"خطا در ارسال جزوه: {str(e)}. لطفاً دوباره تلاش کنید."
                        )
                else:
                    error_msg = "فایل جزوه یافت نشد."
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=error_msg
                    )
                    
            except Exception as e:
                logger.error(f"Error in send_note: {e}")
                if update.callback_query:
                    await update.callback_query.answer(f"خطا: {str(e)}", show_alert=True)
                else:
                    await update.message.reply_text(f"خطا: {str(e)}")
            return RATING

    async def about(self, update: Update, context: CallbackContext) -> int:
        """Show about information."""
        query = update.callback_query
        await query.answer()

        about_text = (
            "📚 *بات جزوه‌های دانشگاهی*\n\n"
            "این ربات به دانشجویان کمک می‌کند تا جزوه‌های درسی را به اشتراک بگذارند و به آنها دسترسی داشته باشند.\n\n"
            "امکانات:\n"
            "• مرور جزوه‌ها بر اساس رشته، نیمسال و درس\n"
            "• امتیازدهی به جزوه‌ها برای کمک به دیگران در یافتن محتوای با کیفیت\n"
            "• دریافت اعلان برای جزوه‌های جدید\n\n"
            "ساخته شده با ❤️ توسط V, برای شما عزیزان"
        )

        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(
            about_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CHOOSING 