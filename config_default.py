SERVER_ADDRESS = ''  # Game server IP
SERVER_PORT = 27016  # Query port
SERVER_POLL_RATE = 5  # Max query rate, in seconds

# See https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
TIMEZONE = 'America/Argentina/Buenos_Aires'

WONITOR_URL = 'http://example.com/wonitor/'
NS2STATS_DB_URL = 'http://example.com/wonitor/data/ns2plus.sqlite3'
NS2STATS_ENABLE_UPDATES = True

DISCORD_TOKEN = ''  # App token
DISCORD_CHANNEL = ''  # Channel ID (number)
ENABLE_STARTUP_MSG = True

BOT_ICON_URL = 'https://i.imgur.com/DsxGVnu.jpg'

# Send alerts to @everyone trying to get more people in, only when threshold min < player count < threshold max
ALERT_EVERYONE_ENABLED = True
ALERT_EVERYONE_THRESHOLD_MIN = 7
ALERT_EVERYONE_THRESHOLD_MAX = 12

# Player count when to consider the game has started
ALERT_PLAYERCOUNT_START = 12

# Cap @everyone alerts to prevent spamming, in seconds
ALERT_EVERYONE_TIME_CAP = 300

# Send a RIP alert when everyone left the server after a successful ALERT_PLAYERCOUNT_START
ALERT_EVERYONE_RIP = True
