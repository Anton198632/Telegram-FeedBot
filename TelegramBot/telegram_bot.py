from datetime import datetime

from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup, Update, Bot
from telegram.ext import Updater, Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, \
    CallbackContext

from TelegramBot.logics import add_new_user, get_main_menu, handle_text_mess, handler_inline_buttons, broadcast_forward
from constants import TOKEN


class TelegramBot:
    __is_started = False
    __ERROR_BIG_FILE = 'Ошибка: размер файла не должен превышать 20 MByte'
    __USER_ANTI_BOT = None
    __DURATION_SECONDS = 1

    __media_group_ids = []

    bot: Bot = None

    def __init__(self):

        self.__USER_ANTI_BOT = {}

        TelegramBot.bot = Bot(TOKEN)
        self.updater: Updater = Updater(TOKEN)
        self.dispatcher: Dispatcher = self.updater.dispatcher

        self.start_handler = CommandHandler('start', self.command_handler)
        self.dispatcher.add_handler(self.start_handler)

        self.messages_handler: MessageHandler = MessageHandler(filters=Filters.text, callback=self.text_message_handler)
        self.dispatcher.add_handler(self.messages_handler)

        self.inline_button_handlers: CallbackQueryHandler = CallbackQueryHandler(callback=self.inline_button_handler)
        self.dispatcher.add_handler(self.inline_button_handlers)

        self.all: MessageHandler = MessageHandler(filters=Filters.all, callback=self.all_handler)
        self.dispatcher.add_handler(self.all)

    def start_request_processing(self):

        print('Бот запущен...')
        self.updater.start_polling(poll_interval=2)
        self.updater.idle()

    def anti_robot_check(self, update) -> bool:
        last_time_request = self.__USER_ANTI_BOT.get(update.effective_message.chat_id)
        if last_time_request is None \
                or (datetime.now() - last_time_request).total_seconds() > self.__DURATION_SECONDS:
            self.__USER_ANTI_BOT[update.effective_message.chat_id] = datetime.now()
            return True
        else:
            # log_message_error('spam', update)
            return False

    # ------------- ОБРАБОТЧИКИ -----------------------------------------------
    # --------- КОМАНДЫ ---------------------------------------------------
    def command_handler(self, update: Update, context: CallbackContext):
        if self.anti_robot_check(update):
            # log_message_incoming(update)
            add_new_user(update)
            get_main_menu(self, update)

    # -------- ТЕКСТ ------------------------------------------------------
    def text_message_handler(self, update: Update, context: CallbackContext):
        broadcast_forward(update)
        if self.anti_robot_check(update):
            handle_text_mess(self, update)

    # --------------------------------------------------------------
    def all_handler(self, update: Update, context: CallbackContext):
        broadcast_forward(update)

    # -------- INLINE-КНОПКИ ----------------------------------------------
    def inline_button_handler(self, update: Update, context: CallbackContext):
        if self.anti_robot_check(update):
            # log_message_inline_button(update)
            handler_inline_buttons(self, update)

    # -------- ОТПРАВИТЕЛИ -------------------------------------------------
    # -------- ТЕКСТ -------------------------------------------------------
    def send_text(self, update: Update, text: str):
        # log_message_outgoing(update, text)
        update.effective_message.reply_text(text, parse_mode='HTML')


    @classmethod
    def send_text_by_user_id(cls, user_id, text):
        # log_message_outgoing(user_id, text)
        cls.bot.send_message(chat_id=user_id, text=text)

    # -------- ВИРТУАЛЬНЫЕ КНОПКИ ------------------------------------------
    def send_keyboard_buttons(self, update: Update, text: str, mk_list):
        # log_message_outgoing(update, text)
        update.effective_message.reply_text(text=text, parse_mode='HTML',
                                            reply_markup=ReplyKeyboardMarkup(mk_list, resize_keyboard=True,
                                                                             one_time_keyboard=True))

    # -------- IN-LINE КНОПКИ ------------------------------------------
    def send_inline_buttons(self, update: Update, text: str, mk_list):
        # log_message_outgoing(update, text)
        update.effective_message.reply_text(text=text, parse_mode='HTML',
                                            reply_markup=InlineKeyboardMarkup(mk_list))

    def update_inline_buttons(self, update: Update, mk_list):
        update.effective_message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(mk_list))


