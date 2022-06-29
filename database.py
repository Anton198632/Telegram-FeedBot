import sqlite3

from models import User, TelegramChannel


class Database:
    __database_connection = None

    def __new__(cls):
        if cls.__database_connection is None:
            cls.__database_connection = sqlite3.connect('db.sqlite3', check_same_thread=False)

    @classmethod
    def get_user(cls, id):
        cursor = cls.__database_connection.execute('select * from USERS where id = :id', {'id': id})
        user = cursor.fetchone()
        user_result = None
        if user is not None:
            user_result = User(user[0], user[1], user[2], user[3], user[4], user[5], user[6], user[7], user[8])
        cursor.close()
        return user_result

    @classmethod
    def add_user(cls, user: User):
        if cls.get_user(user.id) is None:
            cls.__database_connection.execute(
                "insert into USERS(ID, FIRST_NAME, LAST_NAME, USERNAME, STATE_) values (:id, :first_name, :last_name, :username, :state_)",
                {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'state_': user.state
                }
            )
            cls.__database_connection.commit()

    @classmethod
    def update_user_state(cls, user_id: int, state: str):
        if cls.get_user(user_id) is not None:
            cls.__database_connection.execute('update USERS set STATE_ = :state_ where ID = :id',
                                              {'state_': state, 'id': user_id})
            cls.__database_connection.commit()

    @classmethod
    def update_user_age(cls, user_id: int, age: str):
        if cls.get_user(user_id) is not None:
            cls.__database_connection.execute('update USERS set AGE = :age where ID = :id', {'age': age, 'id': user_id})
            cls.__database_connection.commit()

    @classmethod
    def update_user_sex(cls, user_id: int, sex: str):
        if cls.get_user(user_id) is not None:
            cls.__database_connection.execute('update USERS set SEX = :sex where ID = :id', {'sex': sex, 'id': user_id})
            cls.__database_connection.commit()

    @classmethod
    def update_user_address(cls, user_id: int, address: str):
        if cls.get_user(user_id) is not None:
            cls.__database_connection.execute('update USERS set ADDRESS = :address where ID = :id',
                                              {'address': address, 'id': user_id})
            cls.__database_connection.commit()

    @classmethod
    def update_user_state_listening(cls, user_id: int, is_listening: int):
        if cls.get_user(user_id) is not None:
            cls.__database_connection.execute('update USERS set IS_LISTENING = :is_listening where ID = :id',
                                              {'is_listening': is_listening, 'id': user_id})
            cls.__database_connection.commit()


    @classmethod
    def get_telegram_channel(cls, chat_id):
        cursor = cls.__database_connection \
            .execute('select * from TELEGRAMCHANNELS where CHAT_ID = :chat_id', {'chat_id': chat_id})
        telegram_channel = cursor.fetchone()
        telegram_channel_result = None
        if telegram_channel is not None:
            telegram_channel_result = TelegramChannel()
            telegram_channel_result.supergroup_id = telegram_channel[0]
            telegram_channel_result.chat_id = telegram_channel[1]
            telegram_channel_result.title = telegram_channel[2]
            telegram_channel_result.user_name = telegram_channel[3]

        cursor.close()
        return telegram_channel_result

    @classmethod
    def check_subscription(cls, bot_client_id, telegram_channel_id):
        cursor = cls.__database_connection \
            .execute(
            'select * from SUBSCRIPTIONS where USER_ID = :user_id and TELEGRAM_CHANNEL_ID = :telegram_channel_id', {
                'user_id': bot_client_id,
                'telegram_channel_id': telegram_channel_id
            })
        telegram_channel = cursor.fetchone()
        cursor.close()
        return telegram_channel is not None

    @classmethod
    def get_subscriptions(cls, telegram_channel_id):
        users = []
        cursor = cls.__database_connection \
            .execute(
            'select * from SUBSCRIPTIONS where TELEGRAM_CHANNEL_ID = :telegram_channel_id', {
                'telegram_channel_id': telegram_channel_id
            })

        user = cursor.fetchone()
        while user is not None:
            users.append(user[0])
            user = cursor.fetchone()
        cursor.close()
        return users

    @classmethod
    def add_new_telegram_channel(cls, telegram_channel: TelegramChannel):
        if cls.get_telegram_channel(telegram_channel.chat_id) is None:
            cls.__database_connection \
                .execute('insert into TELEGRAMCHANNELS(SUPERGROUP_ID, CHAT_ID, TITLE, USER_NAME, LAST_MESSAGE_TIME)'
                         'values (:supergroup_id, :chat_id, :title, :username, :last_message_time)', {
                             'supergroup_id': telegram_channel.supergroup_id,
                             'chat_id': telegram_channel.chat_id,
                             'title': telegram_channel.title,
                             'username': telegram_channel.user_name,
                             'last_message_time': 0
                         })
            cls.__database_connection.commit()

        if not cls.check_subscription(telegram_channel.bot_client_id, telegram_channel.chat_id):
            cls.__database_connection \
                .execute('insert into SUBSCRIPTIONS(USER_ID, TELEGRAM_CHANNEL_ID) '
                         'values (:user_id, :telegram_channel_id)', {
                             'user_id': telegram_channel.bot_client_id,
                             'telegram_channel_id': telegram_channel.chat_id
                         })
            cls.__database_connection.commit()

    @classmethod
    def get_channel_by_username(cls, user_name: str):
        username = user_name.replace('@', '')
        cursor = cls.__database_connection \
            .execute(f'select * from TELEGRAMCHANNELS where  USER_NAME="{username}"')

        telegram_channel = cursor.fetchone()
        telegram_channel_instance = None
        while telegram_channel is not None:
            telegram_channel_instance = TelegramChannel()
            telegram_channel_instance.chat_id = telegram_channel[1]
            telegram_channel_instance.title = telegram_channel[2]
            telegram_channel_instance.user_name = telegram_channel[3]
            telegram_channel_instance.supergroup_id = telegram_channel[0]
            telegram_channel = cursor.fetchone()

        cursor.close()
        return telegram_channel_instance

    @classmethod
    def get_channels(cls, user_id):
        cursor = cls.__database_connection \
            .execute(
            'select TELEGRAM_CHANNEL_ID from SUBSCRIPTIONS where USER_ID = :user_id', {
                'user_id': user_id
            })

        telegram_channels_ids = []
        channel_id = cursor.fetchone()
        while channel_id is not None:
            telegram_channels_ids.append(channel_id[0])
            channel_id = cursor.fetchone()

        if len(telegram_channels_ids) == 0:
            cursor.close()
            return None

        channel_tuple = str(tuple(telegram_channels_ids)).replace(',)', ')')
        query = f'select * from TELEGRAMCHANNELS where  CHAT_ID in {channel_tuple}'

        cursor = cls.__database_connection \
            .execute(query)

        telegram_channels = []
        telegram_channel = cursor.fetchone()
        while telegram_channel is not None:
            telegram_channel_instance = TelegramChannel()
            telegram_channel_instance.chat_id = telegram_channel[1]
            telegram_channel_instance.title = telegram_channel[2]
            telegram_channel_instance.user_name = telegram_channel[3]
            telegram_channel_instance.supergroup_id = telegram_channel[0]
            telegram_channels.append(telegram_channel_instance)
            telegram_channel = cursor.fetchone()

        cursor.close()
        return telegram_channels

    @classmethod
    def del_channel_from_subscriptions(cls, user_id, telegram_channel_id):
        cls.__database_connection \
            .execute('delete from SUBSCRIPTIONS '
                     'where user_id=:user_id and telegram_channel_id=:telegram_channel_id', {
                         'user_id': user_id,
                         'telegram_channel_id': telegram_channel_id
                     })
        cls.__database_connection.commit()
