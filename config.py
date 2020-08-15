from os import getenv

BOT_TOKEN = getenv('BOT_TOKEN')
DOCTORS_GROUP = int(getenv('DOCTORS_GROUP', 0))
RESERVE_CHANNEL = int(getenv('RESERVE_CHANNEL', 0))
