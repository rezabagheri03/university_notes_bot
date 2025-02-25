from ..models.database import Subscription
from telegram.ext import ApplicationBuilder
import asyncio

async def notify_subscribers(note):
    """Notify all subscribers when a new note is uploaded"""
    try:
        # Get all subscribers for the lesson
        subscriptions = Subscription.query.filter_by(
            lesson_id=note.teacher.lesson_id
        ).all()
        
        if not subscriptions:
            return
        
        # Initialize bot
        bot = ApplicationBuilder().token(current_app.config['TELEGRAM_TOKEN']).build()
        
        message = (
            f"📢 New note available!\n\n"
            f"📝 {note.name}\n"
            f"✍️ Author: {note.author}\n"
            f"📅 Date: {note.date_written}\n"
            f"👨‍🏫 Teacher: {note.teacher.name}\n"
        )
        
        if note.description:
            message += f"\n📌 Description:\n{note.description}"
        
        # Notify each subscriber
        for subscription in subscriptions:
            try:
                await bot.send_message(
                    chat_id=subscription.user.telegram_id,
                    text=message
                )
            except Exception as e:
                current_app.logger.error(
                    f"Failed to notify user {subscription.user.telegram_id}: {str(e)}"
                )
                continue
                
    except Exception as e:
        current_app.logger.error(f"Error in notify_subscribers: {str(e)}") 