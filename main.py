import asyncio
import json
import logging
from collections import namedtuple

import aiohttp
import discord

import config
import ns2plus
import templates
import utils
from game_server import GameServer

logger = logging.getLogger(__name__)
utils.logger_formatter(logger)

ServerStatus = namedtuple('ServerStatus', 'info map players')

loop = asyncio.get_event_loop()

client = discord.Client(loop=loop)
channel = None
admin_channel = None

last_match_id = None


@client.event
async def on_ready():
    """ Run after the bot is connected to Discord """

    global channel
    global admin_channel

    logger.info(templates.LOG_BOT_CONNECTED.format(client.user.name, client.user.id))

    channel = client.get_channel(config.DISCORD_CHANNEL)
    admin_channel = client.get_channel(config.DISCORD_ADMIN_CHANNEL)
    if config.ENABLE_STARTUP_MSG == True:
        await client.send_message(channel, templates.MSG_ON_CONNECT)

    asyncio.ensure_future(alerter_watcher())
    asyncio.ensure_future(ns2plus_watcher())


@client.event
async def on_message(message):
    """ Wait for !commands """

    global channel
    global admin_channel

    admin_command = message.channel == admin_channel
    public_command = message.channel == channel or message.channel == admin_channel

    if message.channel == channel or message.channel == admin_channel:
        if message.content.startswith('!'):
            logger.info(templates.LOG_COMMAND_EXEC.format(message))
            if message.content.startswith('!status'):
                status = game_server.status

                await client.send_message(message.channel, embed=templates.StatusEmbed(status))

            elif message.content.startswith('!comm') and public_command and config.ENABLE_STATS:
                params = message.content.split('!comm ')
                try:
                    player = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    await client.send_message(message.channel, embed=templates.CommEmbed(player))

            elif message.content.startswith('!player') and public_command and config.ENABLE_STATS:
                params = message.content.split('!player ')
                try:
                    player = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    await client.send_message(message.channel, embed=templates.PlayerEmbed(player))

            elif message.content.startswith('!ns2id') and admin_command:
                params = message.content.split('!ns2id ')
                try:
                    input = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    await client.send_message(message.channel, embed=templates.NS2IDEmbed(input))

            elif message.content.startswith('!logs') and admin_command and config.ENABLE_FTP_LOGS:
                params = message.content.split('!logs ')
                try:
                    pattern = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    tmp = await client.send_message(message.channel, '...')
                    await client.edit_message(tmp, templates.logs_response(pattern))

            elif message.content.startswith('!awards') and public_command and config.ENABLE_STATS:
                await client.send_message(message.channel, embed=templates.AwardsEmbed())

            elif message.content.startswith('!help') and public_command:
                await client.send_message(message.channel, embed=templates.HelpEmbed())

            else:
                await client.send_message(message.channel, templates.MSG_COMMAND_NOT_RECOGNIZED)


async def on_gameserver_event(event):
    """ Handle Event objects from GameServer.

    Send associated messages to Discord.

    event: class Event
        Attributes:
            type: Type of event, str
            value: Additional data, str
    """

    global channel

    if event.type == 'join':
        await client.send_message(channel, templates.MSG_EVENT_JOIN.format(event.value, **game_server.status.info))

    if event.type == 'quit':
        await client.send_message(channel, templates.MSG_EVENT_QUIT.format(event.value, **game_server.status.info))

    if event.type == 'afk' and config.ENABLE_AFK_EVENT:
        await client.send_message(channel, templates.MSG_EVENT_AFK.format(event.value))

    if event.type == 'nafk' and config.ENABLE_AFK_EVENT:
        await client.send_message(channel, templates.MSG_EVENT_NAFK.format(event.value))

    if event.type == 'map_change':
        await client.send_message(channel, templates.MSG_EVENT_CHANGEMAP.format(event.value))

    if event.type == 'game_start' and config.ALERT_EVERYONE_ENABLED:
        await client.send_message(channel, embed=templates.GameStartEmbed())

    if event.type == 'rip' and config.ALERT_EVERYONE_RIP:
        await client.send_message(channel, embed=templates.GameRipEmbed(event.value))


async def alerter_watcher():
    """ Periodically check if the alerter condition is met. """
    global channel
    while True:
        status = game_server.status
        if config.ALERT_EVERYONE_ENABLED:
            if config.ALERT_EVERYONE_THRESHOLD_MIN < status.info['player_count'] < config.ALERT_EVERYONE_THRESHOLD_MAX:
                needed_players = config.ALERT_PLAYERCOUNT_START - status.info['player_count']
                await client.send_message(channel, embed=templates.AlertEveryoneEmbed(needed_players))
                await asyncio.sleep(config.ALERT_EVERYONE_TIME_CAP)
            else:
                await asyncio.sleep(5)


async def ns2plus_watcher():
    """ Periodically check if there is an updated ns2plus database available """
    global last_match_id

    while True:
        try:
            with aiohttp.ClientSession() as session:
                async with session.get(config.WONITOR_URL + 'query.php?table=RoundInfo&data=count') as r:
                    response = json.loads(await r.read())
                    match_id = int(response[0]['count'])
                    if last_match_id != match_id and last_match_id is not None:
                        if config.ENABLE_DB_UPDATE_MSG:
                            msg = 'Nueva ronda con ID {}. Actualizando DB.'.format(match_id)
                            await client.send_message(admin_channel, embed=templates.ResponseEmbed(msg))
                        await ns2plus.stats.update()
                    last_match_id = match_id
        except Exception as e:
            logger.error(e)
        else:
            await asyncio.sleep(5)


game_server = GameServer(loop, event_handler=on_gameserver_event)

while True:
    try:
        client.run(config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(e)
