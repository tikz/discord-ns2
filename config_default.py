DATABASE = 'SQLITE'  # MYSQL or SQLITE

# The following is relevant only if using SQLITE
SQLITE_DB_URL = 'http://example.com/wonitor/data/ns2plus.sqlite3'
SQLITE_ENABLE_UPDATES = True  # Fetch the whole sqlite db on start and when a new round is added

# The following is relevant only if using MYSQL
MYSQL_HOST = 'example.com'
MYSQL_USER = 'user'
MYSQL_PASS = 'pass'
MYSQL_DB = 'db'

SERVER_ADDRESS = '127.0.0.1'  # Game server IP
SERVER_PORT = 27016  # Query port
SERVER_POLL_RATE = 5  # Max query rate, in seconds

# See https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
TIMEZONE = 'America/Argentina/Buenos_Aires'

DISCORD_TOKEN = ''  # Discord App token
DISCORD_SERVER = ''  # Discord Server ID (number)
DISCORD_MIN_ROLE = 'Admin'  # Minimum role that can run bot commands designated as admin-only. Case sensitive.
DISCORD_DEFAULT_CHANNEL = ''  # Channel ID of the default channel.
DISCORD_LISTEN_CHANNELS = [DISCORD_DEFAULT_CHANNEL, '']  # List of channel IDs that the bot will listen and reply to
DISCORD_NOW_PLAYING = ''
ENABLE_STARTUP_MSG = True
ENABLE_AFK_EVENT = False

ENABLE_STATS = False
WONITOR_URL = 'http://example.com/wonitor/'
USERCONFIG_API_URL = 'http://api.example.com/api.php'
USERCONFIG_SK = 'secret key setted in usermanagement plugin'
USERCONFIG_SV = 'secret value setted in usermanagement plugin'

ENABLE_FTP_LOGS = False
FTP_ADDRESS = ''
FTP_USER = ''
FTP_PASSWORD = ''
FTP_LOGS_PATH = '/config/shine/logs'
LOCAL_LOGS_PATH = './serverlogs/'

WEBSERVER_PORT = 8001

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

if DATABASE == 'SQLITE':
    import sqlite3

    DB = 'ns2plus.sqlite'


    class Database():
        def __init__(self):
            self.db = DB

        def __enter__(self):
            self.conn = sqlite3.connect(self.db)
            self.conn.row_factory = sqlite3.Row
            return self.conn.cursor()

        def __exit__(self, type, value, traceback):
            self.conn.commit()
            self.conn.close()

if DATABASE == 'MYSQL':
    import pymysql.cursors

    class Database():
        def __enter__(self):
            self.conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASS,
                                        db=MYSQL_DB)
            self.cursor = self.conn.cursor()
            return self

        def execute(self, query):
            class Wrapper():
                def __init__(self, cursor, query):
                    self.cursor = cursor
                    self.cursor.execute(query)
                def fetchall(self):
                    columns = [col[0] for col in self.cursor.description]
                    return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            return Wrapper(self.cursor, query)

        def __exit__(self, type, value, traceback):
            self.conn.close()