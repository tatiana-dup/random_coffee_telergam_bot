from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")
TELEGRAM_ID_PROJECT_GROUP=-123456789
TELEGRAM_ID_TEST_GROUP=-123456789


class Settings:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///default.db')


settings = Settings()
