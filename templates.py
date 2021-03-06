﻿LOG_GET = 'GET {}'
LOG_BOT_CONNECTED = 'Bot conectado: {} - {}'
LOG_COMMAND_EXEC = '{0.author} ejecutó el comando {0.content} en {0.channel}'

MSG_ON_CONNECT = ':robot: Iniciado'
MSG_COMMAND_NOT_RECOGNIZED = 'Comando no reconocido. Para ver la lista de comandos: **!help**'
MSG_COMMAND_ERROR = 'Hubo un error al procesar el comando'
MSG_COMMAND_REQUIRES_PARAMS = 'El comando requiere parametros. Para ver la lista de comandos: **!help**'
MSG_ACK = ':white_check_mark:'
MSG_EVENT_JOIN = ':large_blue_circle: **{}** *entró al servidor* ({player_count}/{max_players})'
MSG_EVENT_QUIT = ':red_circle: **{}** *salió del servidor* ({player_count}/{max_players})'
MSG_EVENT_AFK = ':zzz: **{}** *está AFK*'
MSG_EVENT_NAFK = ':zzz: **{}** *ya no está AFK*'
MSG_EVENT_CHANGEMAP = ':large_orange_diamond: *Se cambió el mapa a* **{}**'
MSG_EVENT_ROUNDSTART = ':small_red_triangle: *Inicio de la ronda*'
MSG_EVENT_ALIENWIN = ':kharaa: *Aliens win*'
MSG_EVENT_MARINEWIN = ':tsf: *Marines win*'
MSG_CHAT = ':speech_balloon: [{}] **{}**: {}'
POST_RESPONSE_CHAT = 'chat{}{}'
POST_RESPONSE_RCON = 'rcon{}{}'

import json
import requests
import utils
import ns2plus
import config
from discord import Embed
import pytz
import logging
import datetime

tz = pytz.timezone(config.TIMEZONE)

logger = logging.getLogger(__name__)
utils.logger_formatter(logger)


def NameToNS2ID(player):
    try:
        player_stats = ns2plus.stats.get_player_stats(player)
    except:
        return False
    else:
        return player_stats['Steam ID']


class HelpEmbed(Embed):
    def __init__(self):
        super().__init__()

        self.set_author(name='Lista de comandos', icon_url=config.BOT_ICON_URL)
        self.description = '**!status** \t\t\t Estado del servidor\n'
        if config.ENABLE_STATS:
            self.description += '**!player** *nick* \tVer estadísticas alien y marine del jugador\n'
            self.description += '**!comm** *nick* \t Ver estadísticas de commander marine del jugador\n'
            self.description += '**!top10** *kdr/rifle/shotgun/melee/comm* \t Ver el respectivo top 10 de jugadores\n'
            self.description += '**!awards**\n'
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
        self.add_field(
            name='Slots', value='{player_count}/{max_players}'.format(**status.info), inline=True)

        if players:
            scoreboard = ''
            for row in players:
                name, score, duration = row
                m, s = divmod(duration, 60)
                h, m = divmod(m, 60)
                formatted_duration = '%d:%02d:%02d' % (h, m, s)

                scoreboard += '{0} \t {1} \n'.format(formatted_duration, name)
            self.add_field(name='Jugadores', value=scoreboard, inline=False)

        self.set_footer(
            text='https://github.com/Tikzz/discord-ns2', icon_url='')
        self.timestamp = datetime.datetime.now(tz)

        if status.map in utils.map_thumbnails:
            self.set_thumbnail(url=utils.map_thumbnails[status.map])


class AlertEveryoneEmbed(Embed):
    def __init__(self, needed_players):
        super().__init__()

        self.description = ':warning: Falta{} **{}** jugador{} para arrancar @everyone'.format(
            'n' if needed_players > 1 else '',
            needed_players,
            'es' if needed_players > 1 else '')
        self.color = 0xD0021B


class GameStartEmbed(Embed):
    def __init__(self):
        super().__init__()

        self.title = 'Arrancamos! 12 jugadores'
        self.description = '@everyone'
        self.color = 0xD0021B
        self.set_thumbnail(
            url='http://i1.kym-cdn.com/photos/images/newsfeed/000/242/631/382.gif')


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
        self.set_thumbnail(
            url='https://www.galabid.com/wp-content/uploads/2017/11/rip-gravestone-md.png')


class CommEmbed(Embed):
    def __init__(self, player):
        super().__init__()
        self.set_author(name=player, icon_url=config.BOT_ICON_URL)
        try:
            comm_stats = ns2plus.stats.get_comm_stats(player)
            self.set_author(
                name=comm_stats['Name'], icon_url=config.BOT_ICON_URL)
            self.add_field(name='Win rate',
                           value=comm_stats['Wins'], inline=False)

            for key in comm_stats['supplies'].keys():
                self.add_field(
                    name=key, value=comm_stats['supplies'][key], inline=True)

            self.set_thumbnail(
                url='https://s3.amazonaws.com/ns2-wiki/thumb/8/82/TSF_logo.png/100px-TSF_logo.png')

            self.set_footer(
                text='Hive Skill: {} - Steam ID: {}'.format(
                    comm_stats['Hive Skill'], comm_stats['Steam ID']),
                icon_url='')
            self.timestamp = datetime.datetime.now(tz)
        except Exception as e:
            self.description = 'No se encuentra el jugador.'
            logger.error(repr(e))


class PlayerEmbed(Embed):
    def __init__(self, player):
        super().__init__()
        self.set_author(name=player, icon_url=config.BOT_ICON_URL)

        try:
            player_stats = ns2plus.stats.get_player_stats(player)
            self.set_author(
                name=player_stats['Name'], icon_url=config.BOT_ICON_URL)

            self.add_field(name='Marine win rate',
                           value=player_stats['Marine Wins'], inline=True)
            self.add_field(name='Alien win rate',
                           value=player_stats['Alien Wins'], inline=True)
            self.add_field(name='KDR', value=player_stats['KDR'], inline=True)
            self.add_field(
                name='PDDR', value=player_stats['PDDR'], inline=True)

            # Spacer
            self.add_field(name=' ‏‏‎ ', value=' ‏‏‎ ', inline=False)

            if 'Marine Accuracy' in player_stats:
                self.add_field(
                    name='Marine Accuracy', value=player_stats['Marine Accuracy'], inline=False)

            for key in player_stats['marine'].keys():
                self.add_field(
                    name=key, value=player_stats['marine'][key], inline=True)

            # Spacer
            self.add_field(name=' ‏‏‎ ', value=' ‏‏‎ ', inline=False)

            if 'Alien Melee Accuracy' in player_stats:
                self.add_field(name='Alien Melee Accuracy',
                               value=player_stats['Alien Melee Accuracy'], inline=False)

            for key in player_stats['alien'].keys():
                self.add_field(
                    name=key, value=player_stats['alien'][key], inline=True)

            if 'Lifeform' in player_stats:
                if player_stats['Lifeform'] == 'Gorge':
                    self.set_thumbnail(url='https://i.imgur.com/c70RH1h.png')
                elif player_stats['Lifeform'] == 'Lerk':
                    self.set_thumbnail(url='https://i.imgur.com/sVBC13I.png')
                elif player_stats['Lifeform'] == 'Fade':
                    self.set_thumbnail(url='https://i.imgur.com/aSNNlVp.png')
                elif player_stats['Lifeform'] == 'Onos':
                    self.set_thumbnail(url='https://i.imgur.com/2hkRdQa.png')
                else:
                    self.set_thumbnail(
                        url='https://s3.amazonaws.com/ns2-wiki/thumb/7/7c/MAC.png/70px-MAC.png')

            # Spacer
            self.add_field(name=' ‏‏‎ ', value=' ‏‏‎ ', inline=False)

            self.set_footer(
                text='Hive Skill: {} - Steam ID: {}'.format(
                    player_stats['Hive Skill'], player_stats['Steam ID']),
                icon_url='')
            self.timestamp = datetime.datetime.now(tz)
        except Exception as e:
            print(repr(e))
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
            self.description = 'NS2ID: **{}**'.format(
                utils.steam64_ns2id(input))
        except:
            self.description = 'No se reconoce la entrada.'
        self.color = 0xD0021B


class AddPlayerEmbed(Embed):
    def __init__(self, input, author):
        super().__init__()
        try:
            author_name = author.name
        except:
            author_name = author.nick

        ns2id = utils.steam64_ns2id(input)
        if ns2id:
            try:
                data = {'ID': str(ns2id), 'Data': {
                    'Group': 'player', 'Author': author_name, 'Input': input}}
                print(data)
                payload = {'operation': 'EDIT_USER', 'data': json.dumps(data),
                           config.USERCONFIG_SK: config.USERCONFIG_SV}
                print(payload)
                r = requests.post('http://ns2api.lag.party',
                                  data=payload).json()
            except:
                self.description = 'No se pudo conectar al servidor.'
            else:
                print(r)
                if r['success'] == True:
                    self.description = '**Agregado NS2ID {}** a la lista de jugadores habilitados.'.format(
                        ns2id)
                else:
                    self.description = 'Hubo un error. {}'.format(r['msg'])
        else:
            self.description = 'No se pudo calcular el NS2ID del jugador.'

        self.color = 0xD0021B


class DelPlayerEmbed(Embed):
    def __init__(self, input):
        super().__init__()
        try:
            data = {'ID': str(input), 'Data': {'Group': 'player'}}
            payload = {'operation': 'REMOVE_USER', 'data': json.dumps(data),
                       config.USERCONFIG_SK: config.USERCONFIG_SV}
            print(payload)
            r = requests.post('http://ns2api.lag.party', data=payload).json()
        except:
            self.description = 'No se pudo conectar al servidor.'
        else:
            print(r)
            if r['success'] == True:
                self.description = '**Eliminado NS2ID {}** de la lista de jugadores habilitados.'.format(
                    input)
            else:
                self.description = 'No se pudo eliminar. {} (¿lo que pusiste es un NS2ID capo?)'.format(
                    r['msg'])

        self.color = 0xD0021B


class TopEmbed(Embed):
    def __init__(self, type):
        super().__init__()
        try:
            top = ns2plus.stats.get_top(type)
        except:
            self.description = 'No se encontro el top 10 para **{}**.'.format(
                type)
        else:
            if type == 'kdr':
                self.set_author(name='TOP 10 Kills/deaths',
                                icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >20 partidas'
            if type == 'melee':
                self.set_author(
                    name='TOP 10 Melee accuracy promedio ponderado', icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >20 partidas'
            if type == 'rifle':
                self.set_author(name='TOP 10 Rifle accuracy',
                                icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >20 partidas'
            if type == 'shotgun':
                self.set_author(name='TOP 10 Shotgun accuracy',
                                icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >20 partidas'
            if type == 'comm':
                self.set_author(name='TOP 10 Commander winrate',
                                icon_url=config.BOT_ICON_URL)
                self.title = 'Para jugadores con >10 partidas'
            try:
                self.description = '\n'.join(top)
            except:
                self.description = 'Hubo un error al obtener el top 10.'
        self.color = 0x66D9EF


class AwardsEmbed(Embed):
    def __init__(self):
        super().__init__()
        self.set_author(name='Awards', icon_url=config.BOT_ICON_URL)

        awards = ns2plus.stats.get_awards()

        self.description = ''

        self.description += '**THE MEATGRINDER** \n'
        self.description += '{1} almas sacrificadas al dios {0}. \n\n'.format(
            *awards['killing_place'])

        self.description += '**El Hombre Omelette** \n'
        self.description += '`{}` pisó {} huevos con alguien respawneando. \n\n'.format(
            *awards['exo_egg'])

        self.description += '**Big Game Hunter** \n'
        self.description += '`{}` mató {} onos. \n\n'.format(
            *awards['onos_killer'])

        self.description += '**If It Bleeds...** \n'
        self.description += '`{}` mató {} fades. \n\n'.format(
            *awards['fade_killer'])

        self.description += '**No Fly Zone** \n'
        self.description += '`{}` mató {} lerks. \n\n'.format(
            *awards['lerk_killer'])

        self.description += '**The Handyman** \n'
        self.description += '`{}` mató a {} con welder. \n\n'.format(
            *awards['welder_kills'])

        self.description += '**parasite** \n'
        self.description += '`{}` mató a {} con parasite. \n\n'.format(
            *awards['parasite_kills'])

        self.description += '**Colgate pls** \n'
        self.description += '`{}` mató a {} con spray de gorge. \n\n'.format(
            *awards['spray_kills'])

        self.description += '**Dungeon Master** \n'
        self.description += '`{}` mató a {} con whips. \n\n'.format(
            *awards['whip_kills'])

        self.description += '**100% accuracy** \n'
        self.description += '`{}` mató a {} con sentries. \n\n'.format(
            *awards['sentry_kills'])

        self.description += '**Pearl Harbor** \n'
        self.description += '`{}` lerkeó, mató a 1 y perdió la lifeform, todo en {}. \n\n'.format(
            *awards['1_kill_lerk'])

        self.description += '**The Boomstick Award** \n'
        self.description += '`{}` sacó shotguns en {} (y {}). \n\n'.format(
            *awards['shotgun_tech'])

        self.description += '**Zerg Rush** \n'
        self.description += '`{}` sacó segunda hive en {} (y {}). \n\n'.format(
            *awards['2nd_hive'])

        self.description += '**La primera es gratis** \n'
        self.description += '`{}` sacó catpacks en {} (y {}). \n\n'.format(
            *awards['catpack_tech'])

        self.description += '**GOLIATH ONLINE** \n'
        self.description += '`{}` sacó exos en {} (y {}). \n\n'.format(
            *awards['exo_tech'])

        self.description += '**Come Fly with Me** \n'
        self.description += '`{}` sacó jetpacks en {} (y {}). \n\n'.format(
            *awards['jp_tech'])

        self.description += '**El Demoledor** \n'
        self.description += '`{}` sacó grenade launcher en {} (y {}). \n\n'.format(
            *awards['gl_tech'])

        self.description += '**GladOS** \n'
        self.description += '`{}` tiró el primer phase gate en {} (y {}). \n\n'.format(
            *awards['phase_gate'])

        self.description += '**Drop that Bass** \n'
        self.description += '`{}` sacó el primer ARC en {} (y {}). \n\n'.format(
            *awards['arc'])

        self.description += '**El kick mas rápido del oeste** \n'
        self.description += '`{}` se metió a commear y lo rajaron en {}. \n\n'.format(
            *awards['commander_eject'])

        self.timestamp = datetime.datetime.now(tz)
