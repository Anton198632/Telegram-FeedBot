import datetime
import os
import threading
import time
from ctypes.util import find_library
from ctypes import *
import json
import sys
from typing import List

# load shared library
from time import sleep

from constants import BUFFER_CHAT_ID, _TEXT_ERROR_CHANNEL, _TEXT_YOU_SUBSCRIPTION_IN_NEW_CHANNEL
from database import Database
from models import TelegramChannel

SESSION = ''

path = os.path.dirname(os.path.realpath((__file__)))
dll = os.path.join(path, 'tdjson.dll')
tdjson = CDLL(dll)

# load TDLib functions from shared library
_td_create_client_id = tdjson.td_create_client_id
_td_create_client_id.restype = c_int
_td_create_client_id.argtypes = []

_td_receive = tdjson.td_receive
_td_receive.restype = c_char_p
_td_receive.argtypes = [c_double]

_td_send = tdjson.td_send
_td_send.restype = None
_td_send.argtypes = [c_int, c_char_p]

_td_execute = tdjson.td_execute
_td_execute.restype = c_char_p
_td_execute.argtypes = [c_char_p]

log_message_callback_type = CFUNCTYPE(None, c_int, c_char_p)

_td_set_log_message_callback = tdjson.td_set_log_message_callback
_td_set_log_message_callback.restype = None
_td_set_log_message_callback.argtypes = [c_int, log_message_callback_type]


# initialize TDLib log with desired parameters
@log_message_callback_type
def on_log_message_callback(verbosity_level, message):
    if verbosity_level == 0:
        sys.exit('TDLib fatal error: %r' % message)


def td_execute(query):
    query = json.dumps(query).encode('utf-8')
    result = _td_execute(query)
    if result:
        result = json.loads(result.decode('utf-8'))
    return result


_td_set_log_message_callback(2, on_log_message_callback)

# create client
client_id = _td_create_client_id()


def td_send(query):
    query = json.dumps(query).encode('utf-8')
    _td_send(client_id, query)


def td_receive():
    result = _td_receive(1.0)
    if result:
        result = json.loads(result.decode('utf-8'))
    return result


# setting TDLib log verbosity level to 1 (errors)
print(str(td_execute({'@type': 'setLogVerbosityLevel', 'new_verbosity_level': 1, '@extra': 1.01234})).encode('utf-8'))

# start the client by sending request to it
td_send({'@type': 'getAuthorizationState', '@extra': 1.01234})

client = None

channel_list: List[TelegramChannel] = []

bot_response = [None]


def get_channel_info_by_username(bot_client_id, user_name: str, handler):
    bot_response[0] = handler
    # user_name = user_name.replace('@', '')

    if not any(bot_client_id == channel.bot_client_id
               and user_name == channel.user_name
               for channel in channel_list):
        telegram_channel = TelegramChannel()
        telegram_channel.bot_client_id = bot_client_id
        telegram_channel.user_name = user_name

        telegram_channel_old = Database.get_channel_by_username(user_name)
        if telegram_channel_old is not None:
            telegram_channel.supergroup_id = telegram_channel_old.supergroup_id

        channel_list.append(telegram_channel)

    td_send({'@type': 'searchPublicChat', 'username': user_name, '@extra': user_name})


def listen_update():
    global channel_list
    start_datetime = datetime.datetime.now()
    while True:

        event = td_receive()
        if event:
            if event['@type'] == 'updateReactions':
                pass

            print(event)
            # ------------ Авторизация ---------------------------------------------------
            if event['@type'] == 'updateAuthorizationState':
                auth_state = event['authorization_state']

                # if client is closed, we need to destroy it and create new client
                if auth_state['@type'] == 'authorizationStateClosed':
                    break

                # set TDLib parameters
                # you MUST obtain your own api_id and api_hash at https://my.telegram.org
                # and use them in the setTdlibParameters call
                if auth_state['@type'] == 'authorizationStateWaitTdlibParameters':
                    with open('TelegramBot\\phone.txt', 'r') as f:
                        SESSION = f.read()

                    td_send({'@type': 'setTdlibParameters', 'parameters': {
                        'database_directory': SESSION,  # 'tdlib'
                        'use_chat_info_database': True,  # +
                        'use_message_database': True,
                        'use_secret_chats': True,
                        'api_id': 94575,
                        'api_hash': 'a3406de8d171bb422bb6ddf3bbd800e2',
                        'system_language_code': 'en',
                        'device_model': 'Desktop',
                        'application_version': '1.0',
                        'enable_storage_optimizer': False,
                        'ignore_file_names': False  # +
                    }})

                # set an encryption key for database to let know TDLib how to open the database
                if auth_state['@type'] == 'authorizationStateWaitEncryptionKey':
                    # pass
                    td_send({'@type': 'checkDatabaseEncryptionKey', 'encryption_key': ''})

                # enter phone number to log in
                if auth_state['@type'] == 'authorizationStateWaitPhoneNumber':
                    phone_number = input('Please enter your phone number: ')
                    td_send({'@type': 'setAuthenticationPhoneNumber', 'phone_number': phone_number})

                # wait for authorization code
                if auth_state['@type'] == 'authorizationStateWaitCode':
                    code = input('Please enter the authentication code you received: ')
                    td_send({'@type': 'checkAuthenticationCode', 'code': code})

                # wait for first and last name for new users
                if auth_state['@type'] == 'authorizationStateWaitRegistration':
                    first_name = input('Please enter your first name: ')
                    last_name = input('Please enter your last name: ')
                    td_send({'@type': 'registerUser', 'first_name': first_name, 'last_name': last_name})

                # wait for password if present
                if auth_state['@type'] == 'authorizationStateWaitPassword':
                    password = input('Please enter your password: ')
                    td_send({'@type': 'checkAuthenticationPassword', 'password': password})

                if auth_state['@type'] == 'authorizationStateReady':
                    pass

            if event['@type'] == 'ok':
                td_send({'@type': 'getMe'})
                # td_send({'@type': 'getChats', 'limit': '200'})

            if event['@type'] == 'user':
                telegram_id = event.get('id')
                first_name = event.get('first_name')
                last_name = event.get('last_name')
                user_name = event.get('username')
                phone_number = event.get('phone_number')
                photo = None
                u_photo = event.get('profile_photo')
                if u_photo is not None:
                    photo = u_photo.get('minithumbnail').get('data')
                if photo is None:
                    photo = ''

            # handle an incoming update or an answer to a previously sent request
            sys.stdout.flush()

            # --------------------- Новое сообщение --------------------------
            if event.get('@type') == 'updateNewMessage':
                d = event.get('message').get('date')

                message_id = event.get('message').get('id')
                chat_id = event.get('message').get('chat_id')

                date_time = datetime.datetime.fromtimestamp(d)

                if date_time > start_datetime:
                    if BUFFER_CHAT_ID != chat_id:
                        td_send({
                            '@type': 'forwardMessages',
                            'chat_id': BUFFER_CHAT_ID,
                            'from_chat_id': chat_id,
                            'message_ids': [message_id]
                        })

            if event.get('@type') == 'messages':
                pass

            # ----------------- Информация о чате по chat_id ---------------------------------
            if event.get('@type') == 'updateNewChat':

                supergroup_id = event.get('chat').get('type').get('supergroup_id')
                chat_id = event.get('chat').get('id')
                title = event.get('chat').get('title')

                if any(supergroup_id == channel.supergroup_id for channel in channel_list):
                    for channel in channel_list:
                        if channel.supergroup_id == supergroup_id:
                            channel.title = title
                            channel.chat_id = chat_id
                            channel.write_to_database(Database)
                            bot_response[0].send_message(
                                channel.bot_client_id,
                                _TEXT_YOU_SUBSCRIPTION_IN_NEW_CHANNEL.replace('TITLE', channel.title),
                                'HTML')
                            td_send({'@type': 'joinChat', 'chat_id': chat_id})

                channel_list = list(filter(lambda x: x.supergroup_id != supergroup_id, channel_list))
                pass

            if event.get('@type') == 'chat':

                supergroup_id = event.get('type').get('supergroup_id')
                chat_id = event.get('id')
                title = event.get('title')

                if any(supergroup_id == channel.supergroup_id for channel in channel_list):
                    for channel in channel_list:
                        if channel.supergroup_id == supergroup_id:
                            channel.title = title
                            channel.chat_id = chat_id
                            channel.write_to_database(Database)
                            bot_response[0].send_message(
                                channel.bot_client_id,
                                _TEXT_YOU_SUBSCRIPTION_IN_NEW_CHANNEL.replace('TITLE', channel.title),
                                'HTML')
                            td_send({'@type': 'joinChat', 'chat_id': chat_id})

                channel_list = list(filter(lambda x: x.supergroup_id != supergroup_id, channel_list))
                pass

            # ---------- Информация о канале -------------------------------
            if event.get('@type') == 'updateSupergroup':
                id_ = event.get('supergroup').get('id')
                user_name = event.get('supergroup').get('username')

                # if not any(id_ == channel.supergroup_id for channel in channel_list):
                for channel in channel_list:
                    if channel.user_name == f'@{user_name}':
                        channel.user_name = user_name
                        channel.supergroup_id = id_

            # ---------- Error -----------------------------------------------
            if event.get('@type') == 'error':
                message = event.get('message')
                if message == 'USERNAME_NOT_OCCUPIED':
                    channel_name = event.get('@extra')
                    for channel in channel_list:
                        if channel.user_name == channel_name:
                            user_id = channel.bot_client_id
                            bot_response[0].send_message(user_id, _TEXT_ERROR_CHANNEL)


thread = threading.Thread(target=listen_update)
thread.start()
