from TelegramBot import telegram_client
from TelegramBot.telegram_bot import TelegramBot
from database import Database

if __name__ == '__main__':
    Database()

    telegram_bot = TelegramBot()
    telegram_bot.start_request_processing()








