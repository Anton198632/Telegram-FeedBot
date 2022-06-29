import asyncio
import datetime

from telegram import Update
import json
from telegram.ext import CallbackContext

from TelegramBot.keyboard import Keyboards

from TelegramBot.telegram_client import get_channel_info_by_username
from constants import BUFFER_CHAT_ID, _TEXT_MAIN_MENU, _TEXT_YOU_SUBSCRIPTIONS, _TEXT_CHANGE_SUBSCRIPTIONS, \
    _TEXT_SET_INTERESTS, _TEXT_FEED_STARTED, _TEXT_FEED_STOP, _TEXT_BOT_INFORMATION, _TEXT_DEFAULT, _TEXT_SET_SEX, \
    _TEXT_SET_AGE, _TEXT_SET_ADDRESS, _TEXT_INPUT_CHANNEL_NAME, _TEXT_OK, _CHANGE_SUBSCRIPTIONS, _CHANGE_INTERESTS, \
    _BOT_INFORMATION, _CONFIRM, _START_FEED, _STOP_FEED, _WRITE_A_FEEDBACK, _SEX, _AGE, _ADDRESS, _ADD_CHANNEL, \
    _CHANGE_CHANNELS, _TEXT_NOT_CHANNELS
from database import Database
from models import User

__STATES = [
    'main_menu',
    'set_sex',
    'set_age',
    'set_address',
]


def add_new_user(update: Update):
    user = User(
        id=update.effective_message.chat_id,
        username=update.effective_message.chat.username if update.effective_message.chat.username is not None else '',
        first_name=update.effective_message.chat.first_name if update.effective_message.chat.first_name is not None else '',
        last_name=update.effective_message.chat.last_name if update.effective_message.chat.last_name is not None else '',
    )
    Database.add_user(user)


def update_user_state(update: Update, state: str):
    if update.effective_message is not None:
        Database.update_user_state(user_id=update.effective_message.chat_id, state=state)


def get_main_menu(telegram_bot, update: Update):
    update_user_state(update, 'main_menu')
    telegram_bot.send_keyboard_buttons(update, _TEXT_MAIN_MENU, Keyboards.main_menu_get_keyboard())


def broadcast_forward(update: Update):
    if update.effective_message.sender_chat is not None and update.effective_message.sender_chat.id == BUFFER_CHAT_ID:

        subscriptions_ids = Database.get_subscriptions(
            update.effective_message.forward_from_chat.id
            if update.effective_message.forward_from_chat is not None else update.effective_message.forward_from.id

        )

        for user_id in subscriptions_ids:
            user = Database.get_user(user_id)
            if user.is_listening == 1:
                update.effective_message.forward(user.id)


def edit_channels(telegram_bot, update, offset=0, update_buttons=False):
    telegram_channels = Database.get_channels(update.effective_message.chat_id)

    if telegram_channels is None:
        update.effective_message.reply_text(_TEXT_NOT_CHANNELS)
        return

    if not update_buttons:
        telegram_bot.send_inline_buttons(update, _TEXT_YOU_SUBSCRIPTIONS,
                                         Keyboards.edit_channels_list(telegram_channels, offset))
    else:
        telegram_bot.update_inline_buttons(update, Keyboards.edit_channels_list(telegram_channels, offset))


class Handler():
    telegram_bot = None

    def __init__(self, telegram_bot):
        self.telegram_bot = telegram_bot

    def send_message(self, user_id, message_text, parse_mode='HTML'):
        self.telegram_bot.bot.send_message(chat_id=user_id, text=message_text, parse_mode=parse_mode)


def handle_text_mess(telegram_bot, update: Update):
    text = update.effective_message.text
    user = Database.get_user(id=update.effective_message.chat_id)

    if user is None:
        return

    if text == _CHANGE_SUBSCRIPTIONS:
        telegram_bot.send_keyboard_buttons(update, _TEXT_CHANGE_SUBSCRIPTIONS,
                                           Keyboards.change_subscriptions_get_keyboard())

    elif text == _CHANGE_INTERESTS:
        text_set_interest = _TEXT_SET_INTERESTS \
            .replace('TELEGRAM_ID', str(user.id)) \
            .replace('AGE', user.age if user.age is not None else '') \
            .replace('SEX', user.sex if user.sex is not None else '') \
            .replace('ADDRESS', user.address if user.address is not None else '') \
            .replace('IS_LISTENING', _TEXT_FEED_STARTED if user.is_listening == 1 else _TEXT_FEED_STOP)

        telegram_bot.send_keyboard_buttons(update, text_set_interest, Keyboards.set_interests_get_keyboard())

    elif text == _BOT_INFORMATION:
        telegram_bot.send_text(update, _TEXT_BOT_INFORMATION)

    elif text == _CONFIRM:
        telegram_bot.send_keyboard_buttons(update, _TEXT_DEFAULT, Keyboards.main_menu_get_keyboard())

    elif text == _START_FEED:
        Database.update_user_state_listening(update.effective_message.chat_id, 1)
        update.effective_message.reply_text(_TEXT_FEED_STARTED)

    elif text == _STOP_FEED:
        Database.update_user_state_listening(update.effective_message.chat_id, 0)
        update.effective_message.reply_text(_TEXT_FEED_STOP)

    elif text == _WRITE_A_FEEDBACK:
        pass

    elif text == _SEX:
        telegram_bot.send_inline_buttons(update, _TEXT_SET_SEX, Keyboards.set_sex_buttons())
        update_user_state(update, 'set_sex')

    elif text == _AGE:
        telegram_bot.send_text(update, _TEXT_SET_AGE)
        update_user_state(update, 'set_age')

    elif text == _ADDRESS:
        telegram_bot.send_text(update, _TEXT_SET_ADDRESS)
        update_user_state(update, 'set_address')

    elif text == _ADD_CHANNEL:
        telegram_bot.send_text(update, _TEXT_INPUT_CHANNEL_NAME)
        update_user_state(update, 'add_channel')

    elif text == _CHANGE_CHANNELS:
        edit_channels(telegram_bot, update)
        update_user_state(update, 'change_channel')


    else:
        if user.state == 'set_age':
            telegram_bot.send_text(update, _TEXT_OK)
            update_user_state(update, '')
            Database.update_user_age(update.effective_message.chat_id, text)

        if user.state == 'set_address':
            telegram_bot.send_text(update, _TEXT_OK)
            update_user_state(update, '')
            Database.update_user_address(update.effective_message.chat_id, text)

        if user.state == 'add_channel':
            handler_error = Handler(telegram_bot)
            get_channel_info_by_username(update.effective_message.chat_id, text, handler_error)


def handler_inline_buttons(telegram_bot, update: Update):
    data = update.callback_query.data
    user = Database.get_user(id=update.callback_query.from_user.id)

    if 'del_' in data:
        del_channel_id = data[4:]
        Database.del_channel_from_subscriptions(user.id, del_channel_id)
        telegram_channels = Database.get_channels(update.effective_message.chat_id)
        if telegram_channels is not None:
            telegram_bot.update_inline_buttons(update, Keyboards.edit_channels_list(telegram_channels, 0))
        else:
            update.effective_message.reply_text(_TEXT_NOT_CHANNELS)

    if 'offset_' in data:
        offset = int(data[7:])
        edit_channels(telegram_bot, update, offset, True)

    if user.state == 'set_sex':
        if data == 'male':
            Database.update_user_sex(user.id, 'М')
        else:
            Database.update_user_sex(user.id, 'Ж')
