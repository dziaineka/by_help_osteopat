from os import getenv

BOT_TOKEN = getenv('BOT_TOKEN')
DOCTORS_GROUP = getenv('DOCTORS_GROUP')
RESERVE_CHANNEL = int(getenv('RESERVE_CHANNEL', 0))
