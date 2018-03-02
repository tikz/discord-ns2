LOG_GET = 'GET {}'
LOG_BOT_CONNECTED = 'Bot conectado: {} - {}'
LOG_COMMAND_EXEC = '{0.author} ejecutó el comando {0.content} en {0.channel}'

MSG_ON_CONNECT = ':robot: Iniciado'
MSG_COMMAND_NOT_RECOGNIZED = 'Comando no reconocido. Para ver la lista de comandos: **!help**'
MSG_COMMAND_REQUIRES_PARAMS = 'El comando requiere parametros. Para ver la lista de comandos: **!help**'
MSG_EVENT_JOIN = ':large_blue_circle: **{}** *entró al servidor* ({player_count}/{max_players})'
MSG_EVENT_QUIT = ':red_circle: **{}** *salió del servidor* ({player_count}/{max_players})'
MSG_EVENT_AFK = ':zzz: **{}** *está AFK*'
MSG_EVENT_NAFK = ':zzz: **{}** *ya no está AFK*'
MSG_EVENT_CHANGEMAP = ':large_orange_diamond: *Se cambió el mapa a* **{}**'

import datetime
import logging

import pytz
from discord import Embed

import config
import ns2plus
import utils
from server_logs import logs

tz = pytz.timezone(config.TIMEZONE)

logger = logging.getLogger(__name__)
utils.logger_formatter(logger)


class HelpEmbed(Embed):
    def __init__(self):
        super().__init__()

        self.set_author(name='Lista de comandos', icon_url=config.BOT_ICON_URL)
        self.description = '**!status** \t\t\t Estado del servidor\n'
        if config.ENABLE_STATS:
            self.description += '**!player** *nick* \tVer estadísticas alien y marine del jugador\n'
            self.description += '**!comm** *nick* \t Ver estadísticas de commander marine del jugador\n'
            self.description += '**!top10** *kdr/rifle/melee/comm* \t Ver el respectivo top 10 de jugadores\n'
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

                scoreboard += '{0} \t {1} \n'.format(formatted_duration, name)
            self.add_field(name='Jugadores', value=scoreboard, inline=False)

        self.set_footer(text='https://github.com/Tikzz/discord-ns2', icon_url='')
        self.timestamp = datetime.datetime.now(tz)

        if status.map in utils.map_thumbnails:
            self.set_thumbnail(url=utils.map_thumbnails[status.map])


class AlertEveryoneEmbed(Embed):
    def __init__(self, needed_players):
        super().__init__()

        self.description = ':warning: Falta **{}** persona{} para arrancar @everyone'.format(needed_players, 's' if len(
            needed_players) > 1 else '')
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
            self.add_field(name='Win rate', value=comm_stats['Wins'], inline=False)

            for key in comm_stats['supplies'].keys():
                self.add_field(name=key, value=comm_stats['supplies'][key], inline=True)

            self.set_thumbnail(url='https://s3.amazonaws.com/ns2-wiki/thumb/8/82/TSF_logo.png/100px-TSF_logo.png')

            self.set_footer(
                text='Hive Skill: {} - Steam ID: {}'.format(comm_stats['Hive Skill'], comm_stats['Steam ID']),
                icon_url='')
            self.timestamp = datetime.datetime.now(tz)
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
            self.timestamp = datetime.datetime.now(tz)
        except Exception as e:
            self.description = 'No se encuentra el jugador.'
            logger.error(e)


class ResponseEmbed(Embed):
    def __init__(self, description):
        super().__init__()
        self.description = description
        self.color = 0xD0021B


class NS2IDEmbed(Embed):
    def __init__(self, input):
        super().__init__()
        try:
            self.description = 'NS2ID: **{}**'.format(utils.steam64_ns2id(input))
        except:
            self.description = 'No se reconoce la entrada.'
        self.color = 0xD0021B

class TopEmbed(Embed):
    def __init__(self, type):
        super().__init__()
        try:
            top = ns2plus.stats.get_top(type)
        except:
            self.description = 'No se encontro el top 10 para **{}**.'.format(type)
        else:
            if type == 'kdr':
                self.set_author(name='TOP 10 Kills/deaths', icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >20 partidas'
            if type == 'melee':
                self.set_author(name='TOP 10 Melee accuracy promedio ponderado', icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >20 partidas'
            if type == 'rifle':
                self.set_author(name='TOP 10 Rifle accuracy', icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >20 partidas'
            if type == 'comm':
                self.set_author(name='TOP 10 Commander winrate', icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >10 partidas'
            try:
                self.description = '\n'.join(top)
            except:
                self.description = 'Hubo un error al obtener el top 10.'
        self.color = 0x66D9EF

def logs_response(input):
    logs.sync()
    found = logs.search(input)

    if found:
        response = ''
        n_found = len(found)
        response += 'Hay **{}** coincidencia{}.'.format(n_found, 's' if n_found > 1 else '')
        response += ' Mostrando solo las últimas 5.' if n_found > 5 else ''
        response += '\n```{}```'.format('\n'.join(found[::-1][:5]))
        return response
    else:
        return ':warning: No se encuentra.'


class AwardsEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.set_author(name='Awards', icon_url=config.BOT_ICON_URL)

        awards = ns2plus.stats.get_awards()

        self.description = ''

        self.description += '**El rompehuevos** \n'
        self.description += '`{}` pisó {} huevos con alguien respawneando. \n\n'.format(*awards['exo_egg'])

        self.description += '**Saquenlo por cesarea** \n'
        self.description += '`{}` jugó {} de huevo. \n\n'.format(*awards['embryo'])

        self.description += '**Mi clase favorita** \n'
        self.description += '`{}` estuvo {} muerto. \n\n'.format(*awards['dead'])

        self.description += '**THE MEATGRINDER** \n'
        self.description += '{1} almas sacrificadas al dios {0}. \n\n'.format(*awards['killing_place'])

        self.description += '**asd** \n'
        self.description += '`{}` sacó shotguns en {} (y {}). \n\n'.format(*awards['shotgun_tech'])

        self.description += '**asd** \n'
        self.description += '`{}` sacó segunda hive en {} (y {}). \n\n'.format(*awards['2nd_hive'])

        self.description += '**La primera es gratis** \n'
        self.description += '`{}` sacó catpacks en {} (y {}). \n\n'.format(*awards['catpack_tech'])

        self.description += '**asd** \n'
        self.description += '`{}` tiró el primer phase gate en {} (y {}). \n\n'.format(*awards['phase_gate'])

        self.description += '**El kick mas rápido del oeste** \n'
        self.description += '`{}` se metió a commear y lo rajaron en {}. \n\n'.format(*awards['commander_eject'])

        self.timestamp = datetime.datetime.now(tz)
