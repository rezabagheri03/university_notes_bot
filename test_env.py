from dotenv import load_dotenv
import os

print("Current working directory:", os.getcwd())
print("Before loading .env:")
print("TELEGRAM_BOT_TOKEN:", os.getenv('TELEGRAM_BOT_TOKEN'))

load_dotenv()

print("\nAfter loading .env:")
print("TELEGRAM_BOT_TOKEN:", os.getenv('TELEGRAM_BOT_TOKEN'))

# List all environment variables
print("\nAll environment variables:")
for key, value in os.environ.items():
    print(f"{key}: {value}") 