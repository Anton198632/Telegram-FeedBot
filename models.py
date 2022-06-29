


class TelegramChannel:
    def __init__(self):
        self.supergroup_id = 0
        self.chat_id = 0
        self.title = ''
        self.user_name = ''
        self.last_message_time = 0
        self.bot_client_id = 0

    def write_to_database(self, database):
        database.add_new_telegram_channel(self)



class User:
    def __init__(self, id, first_name, last_name, username, state=None, sex=None, age=None, address=None, is_listening=0):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.state = state
        self.age = age
        self.sex = sex
        self.address = address
        self.is_listening = is_listening


class Subscription:
    def __init__(self, user_id, telegram_channel_id):
        self.user_id = user_id
        self.telegram_channel_id = telegram_channel_id
