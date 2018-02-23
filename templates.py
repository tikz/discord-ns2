LOG_GET = 'GET {}'
LOG_BOT_CONNECTED = 'Bot conectado: {} - {}'
LOG_COMMAND_EXEC = '{0.author} ejecutó el comando {0.content}'

MSG_ON_CONNECT = ':robot: Iniciado'
MSG_COMMAND_NOT_RECOGNIZED = 'Comando no reconocido. Para ver la lista de comandos: **!help**'
MSG_COMMAND_REQUIRES_PARAMS = 'El comando requiere parametros. Para ver la lista de comandos: **!help**'
MSG_EVENT_JOIN = ':large_blue_circle: **{}** *entró al servidor*'
MSG_EVENT_QUIT = ':red_circle: **{}** *salió del servidor*'
MSG_EVENT_AFK = ':zzz: **{}** *está AFK*'
MSG_EVENT_NAFK = ':zzz: **{}** *ya no está AFK*'
MSG_EVENT_CHANGEMAP = ':large_orange_diamond: *Se cambió el mapa a* **{}**'

import datetime
import logging

from discord import Embed

import config
import ns2plus
import utils

logger = logging.getLogger(__name__)
utils.logger_formatter(logger)

class HelpEmbed(Embed):
    def __init__(self):
        super().__init__()

        self.set_author(name='Lista de comandos', icon_url=config.BOT_ICON_URL)
        self.description = '**!status** \t\t\t Estado del servidor\n'
        self.description += '**!player** *nick* \tVer estadísticas alien y marine del jugador\n'
        self.description += '**!comm** *nick* \t Ver estadísticas de commander marine del jugador\n'
        self.color = 0xD0021B

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

        self.description = ':warning: Faltan **{}** personas y arrancamos @everyone'.format(needed_players)
        self.color = 0xD0021B


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


class CommEmbed(Embed):
    def __init__(self, player):
        super().__init__()
        self.set_author(name=player, icon_url=config.BOT_ICON_URL)
        try:
            comm_stats = ns2plus.stats.get_comm_stats(player)
            self.set_author(name=comm_stats['Name'], icon_url=config.BOT_ICON_URL)

            for key in comm_stats['supplies'].keys():
                self.add_field(name=key, value=comm_stats['supplies'][key], inline=True)

            self.set_thumbnail(url='https://s3.amazonaws.com/ns2-wiki/thumb/8/82/TSF_logo.png/100px-TSF_logo.png')

            self.set_footer(
                text='Hive Skill: {} - Steam ID: {}'.format(comm_stats['Hive Skill'], comm_stats['Steam ID']),
                icon_url='')
            self.timestamp = datetime.datetime.now()
        except Exception as e:
            self.description = 'No se encuentra el jugador.'
            logger.error(e)


class PlayerEmbed(Embed):
    def __init__(self, player):
        super().__init__()
        self.set_author(name=player, icon_url=config.BOT_ICON_URL)

        try:
            player_stats = ns2plus.stats.get_player_stats(player)
            self.set_author(name=player_stats['Name'], icon_url=config.BOT_ICON_URL)

            self.add_field(name='Win rate', value=player_stats['Wins'], inline=True)
            self.add_field(name='KDR', value=player_stats['KDR'], inline=True)

            # Spacer
            self.add_field(name=' ‏‏‎ ', value=' ‏‏‎ ', inline=False)

            self.add_field(name='Marine Accuracy', value=player_stats['Marine Accuracy'], inline=False)

            for key in player_stats['marine'].keys():
                self.add_field(name=key, value=player_stats['marine'][key], inline=True)

            # Spacer
            self.add_field(name=' ‏‏‎ ', value=' ‏‏‎ ', inline=False)

            self.add_field(name='Alien Melee Accuracy', value=player_stats['Alien Melee Accuracy'], inline=False)

            for key in player_stats['alien'].keys():
                self.add_field(name=key, value=player_stats['alien'][key], inline=True)

            self.set_thumbnail(url='https://s3.amazonaws.com/ns2-wiki/thumb/7/7c/MAC.png/70px-MAC.png')

            self.set_footer(
                text='Hive Skill: {} - Steam ID: {}'.format(player_stats['Hive Skill'], player_stats['Steam ID']),
                icon_url='')
            self.timestamp = datetime.datetime.now()
        except Exception as e:
            self.description = 'No se encuentra el jugador.'
            logger.error(e)
