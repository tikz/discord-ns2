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

last_match_id = None


@client.event
async def on_ready():
    """ Run after the bot is connected to Discord """

    global channel

    logger.info(templates.LOG_BOT_CONNECTED.format(client.user.name, client.user.id))

    channel = client.get_channel(config.DISCORD_CHANNEL)
    await client.send_message(channel, templates.MSG_ON_CONNECT)

    asyncio.ensure_future(watcher())


@client.event
async def on_message(message):
    """ Wait for !commands """

    global channel

    if message.channel == channel:
        if message.content.startswith('!'):
            logger.info(templates.LOG_COMMAND_EXEC.format(message))

        if message.content.startswith('!status'):
            status = game_server.status

            await client.send_message(channel, embed=templates.StatusEmbed(status))

        if message.content.startswith('!comm'):
            params = message.content.split('!comm ')
            player = params[1]
            await client.send_message(channel, embed=templates.CommEmbed(player))

        if message.content.startswith('!player'):
            params = message.content.split('!player ')
            player = params[1]
            await client.send_message(channel, embed=templates.PlayerEmbed(player))


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
        await client.send_message(channel, templates.MSG_EVENT_JOIN.format(event.value))

    if event.type == 'quit':
        await client.send_message(channel, templates.MSG_EVENT_QUIT.format(event.value))

    if event.type == 'afk':
        await client.send_message(channel, templates.MSG_EVENT_AFK.format(event.value))

    if event.type == 'nafk':
        await client.send_message(channel, templates.MSG_EVENT_NAFK.format(event.value))

    if event.type == 'map_change':
        await client.send_message(channel, templates.MSG_EVENT_CHANGEMAP.format(event.value))

    if event.type == 'game_start' and config.ALERT_EVERYONE_ENABLED:
        await client.send_message(channel, embed=templates.GameStartEmbed)

    if event.type == 'rip' and config.ALERT_EVERYONE_RIP:
        await client.send_message(channel, embed=templates.GameRipEmbed(event.value))


async def watcher():
    """ Periodically check if some conditions are met. """

    global channel
    global last_match_id

    while True:
        status = game_server.status
        if config.ALERT_EVERYONE_ENABLED:
            if config.ALERT_EVERYONE_THRESHOLD_MIN < status.info['player_count'] < config.ALERT_EVERYONE_THRESHOLD_MAX:
                needed_players = config.ALERT_PLAYERCOUNT_START - status.info['player_count']
                await client.send_message(channel, embed=templates.AlertEveryoneEmbed(needed_players))
                await asyncio.sleep(config.ALERT_EVERYONE_TIME_CAP)
            else:
                await asyncio.sleep(5)

        with aiohttp.ClientSession() as session:
            async with session.get(config.WONITOR_URL + 'query.php?table=RoundInfo&data=count') as r:
                response = json.loads(await r.read())
                match_id = int(response[0]['count'])
                if last_match_id != match_id and last_match_id is not None:
                    await ns2plus.stats.update()
                last_match_id = match_id


game_server = GameServer(loop, event_handler=on_gameserver_event)

while True:
    try:
        client.run(config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(e)
