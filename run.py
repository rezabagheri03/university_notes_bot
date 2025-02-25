import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application
from app import create_app
from app.bot.handlers import TelegramBotHandlers
import threading
import asyncio
import nest_asyncio
from telegram import Update

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = create_app()

def run_flask():
    """Run the Flask web interface."""
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

async def run_telegram():
    """Run the Telegram bot."""
    # Create bot application
    bot_token = os.getenv('TELEGRAM_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_TOKEN not found in environment variables")
        return

    # Build and configure the application
    application = Application.builder().token(bot_token).build()
    
    try:
        # Create handlers and add them to the application
        handlers = TelegramBotHandlers(app)
        for handler in handlers.get_handlers():
            application.add_handler(handler)

        # Start the bot
        logger.info("Starting bot...")
        await application.initialize()
        await application.start()
        
        # Start polling
        logger.info("Starting polling...")
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Keep the application running
        stop_signal = asyncio.Event()
        await stop_signal.wait()
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        # Ensure proper cleanup
        try:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def main():
    """Main function to run both Flask and Telegram bot."""
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run Telegram bot with proper async handling
    try:
        asyncio.run(run_telegram())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Main error: {e}")

if __name__ == '__main__':
    main() 