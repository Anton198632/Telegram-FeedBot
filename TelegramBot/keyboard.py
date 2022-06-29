from typing import List

from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Location
from telegram.ext import CallbackContext

# # ------------ ОТПРАВИТЕЛИ ------------------------------------------------
# # -------- INLINE-КНОПКИ ----------------------------------------------
from models import TelegramChannel
#
#
# def send_inline_button(chat_id: int, text: str, context: CallbackContext):
#     mk_list = Keyboards.get_inline_keyboard()
#     context.bot.send_message(chat_id=chat_id, text=text,
#                              reply_markup=InlineKeyboardMarkup(mk_list))
#
#
# # -------- КНОПКИ ----------------------------------------------
# def send_keyboard_button(chat_id: int, text: str, context: CallbackContext):
#     mk_list = Keyboards.main_menu_get_keyboard()
#     context.bot.send_message(chat_id=chat_id, text=text,
#                              reply_markup=ReplyKeyboardMarkup(mk_list, resize_keyboard=True, one_time_keyboard=True))


class Keyboards:
    from constants import _CHANGE_SUBSCRIPTIONS, _CHANGE_INTERESTS, _BOT_INFORMATION, \
        _START_FEED, _STOP_FEED, _WRITE_A_FEEDBACK, _ADD_CHANNEL, _CHANGE_CHANNELS, \
        _CONFIRM, _SEX, _AGE, _ADDRESS

    @classmethod
    def main_menu_get_keyboard(cls):
        return [
            [KeyboardButton(text=cls._CHANGE_SUBSCRIPTIONS)],
            [KeyboardButton(text=cls._CHANGE_INTERESTS)],
            [KeyboardButton(text=cls._BOT_INFORMATION)],
            [KeyboardButton(text=cls._START_FEED)],
            [KeyboardButton(text=cls._STOP_FEED)],
            [KeyboardButton(text=cls._WRITE_A_FEEDBACK)]]

    @classmethod
    def change_subscriptions_get_keyboard(cls):
        return [
            [KeyboardButton(text=cls._ADD_CHANNEL)],
            [KeyboardButton(text=cls._CHANGE_CHANNELS)],
            [KeyboardButton(text=cls._CONFIRM)]]

    @classmethod
    def set_interests_get_keyboard(cls):
        return [
            [KeyboardButton(text=cls._SEX)],
            [KeyboardButton(text=cls._AGE)],
            [KeyboardButton(text=cls._ADDRESS)],
            [KeyboardButton(text=cls._CONFIRM)]]

    @classmethod
    def edit_channels_list(cls, channels: List[TelegramChannel], offset: int):

        keyboards = []
        __STEP: int = 5

        counter = 0
        for i in range(offset, offset + __STEP):
            if i < len(channels):
                counter += 1
                keyboards.append(
                    [InlineKeyboardButton(text=channels[i].title, url=f'https://t.me/{channels[i].user_name}'),
                     InlineKeyboardButton(text='удалить', callback_data=f'del_{channels[i].chat_id}')])

        if offset == 0 and counter < len(channels):
            keyboards.append([InlineKeyboardButton(text='>', callback_data=f'offset_{offset + __STEP}')])

        if offset != 0 and offset + __STEP < len(channels):  # counter < len(channels)
            keyboards.append([InlineKeyboardButton(text='<', callback_data=f'offset_{offset - __STEP}'),
                              InlineKeyboardButton(text='>', callback_data=f'offset_{offset + __STEP}')])

        if offset != 0 and offset + __STEP >= len(channels):  # counter == len(channels)
            keyboards.append([InlineKeyboardButton(text='<', callback_data=f'offset_{offset - __STEP}')])

        return keyboards

    @classmethod
    def set_sex_buttons(cls):
        return [[InlineKeyboardButton(text='M', callback_data='male'),
                 InlineKeyboardButton(text='Ж', callback_data='female')]]
