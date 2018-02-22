import datetime

from discord import Embed

import config
from statusbot import utils


class StatusEmbed(Embed):
    def __init__(self, status):
        super().__init__()

        server_name = '**{server_name}**'.format(**status.info)
        players = [(player.values['name'], player.values['score'], player.values['duration'])
                   for player in sorted(status.players, key=lambda p: p["score"], reverse=True)]

        self.description = server_name
        self.color = 0xFD971F
        self.set_author(name='Server Status', icon_url=config.BOT_ICON_URL)
        self.add_field(name='Mapa', value=status.map, inline=True)
        self.add_field(name='Slots', value='{player_count}/{max_players}'.format(**status.info), inline=True)

        if players:
            scoreboard = ''
            for row in players:
                name, score, duration = row
                m, s = divmod(duration, 60)
                h, m = divmod(m, 60)
                formatted_duration = '%d:%02d:%02d' % (h, m, s)

                scoreboard += '{0} \t\t\t\t\t\t {1} \t\t {2} \n'.format(name, score, formatted_duration)
            self.add_field(name='Jugadores', value=scoreboard, inline=False)

        self.set_footer(text='https://github.com/Tikzz/discord-ns2', icon_url='')
        self.timestamp = datetime.datetime.now()

        if status.map in utils.map_thumbnails:
            self.set_thumbnail(url=utils.map_thumbnails[status.map])

class AlertEveryoneEmbed(Embed):
    def __init__(self, needed_players):
        super().__init__()

        self.description=':warning: Faltan **{}** personas y arrancamos @everyone'.format(needed_players)
        self.color=0xD0021B


class GameStartEmbed(Embed):
    def __init__(self):
        super().__init__()

        self.title = 'Arrancamos! 12 jugadores'
        self.description = '@everyone'
        self.color = 0xD0021B
        self.set_thumbnail(url='http://i1.kym-cdn.com/photos/images/newsfeed/000/242/631/382.gif')


class GameRipEmbed(Embed):
    def __init__(self, start_time):
        super().__init__()

        sec = datetime.timedelta(seconds=start_time)
        d = datetime.datetime(1, 1, 1) + sec
        hours = '{} hora'.format(d.hour) if d.hour > 0 else ''
        hours += 's' if d.hour > 1 else ''
        mins = '{} minuto'.format(d.minute) if d.minute > 0 else ''
        mins += 's' if d.minute > 1 else ''
        secs = '{} segundo'.format(d.second) if d.second > 0 else ''
        secs += 's' if d.second > 1 else ''
        lasted = ', '.join([hours, mins, secs])

        self.title = 'Duraron apenas {}'.format(lasted)
        self.description = '0/20 \n\n Ahora pueden seguir jugando Doki Doki'
        self.color = 0xD0021B
        self.set_thumbnail(url='https://www.galabid.com/wp-content/uploads/2017/11/rip-gravestone-md.png')

LOG_BOT_CONNECTED = 'Bot conectado: {} - {}'
LOG_COMMAND_EXEC = '{0.author} ejecutó el comando {0.content}'

MSG_ON_CONNECT = ':robot: Iniciado'
MSG_EVENT_JOIN = ':large_blue_circle: **{}** *entró al servidor*'
MSG_EVENT_QUIT = ':red_circle: **{}** *salió del servidor*'
MSG_EVENT_AFK = ':zzz: **{}** *está AFK*'
MSG_EVENT_NAFK = ':zzz: **{}** *ya no está AFK*'
MSG_EVENT_CHANGEMAP = ':large_orange_diamond: *Se cambió el mapa a* **{}**'
