import asyncio
import json
import logging
import time
from collections import namedtuple

import aiohttp
import discord
from aiohttp import web

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
channel_bans = None
min_role = None

last_match_id = None


@client.event
async def on_ready():
    """ Run after the bot is connected to Discord """

    global channel
    global channel_bans
    global min_role

    logger.info(templates.LOG_BOT_CONNECTED.format(
        client.user.name, client.user.id))

    # Set the given default channels
    channel = client.get_channel(config.DISCORD_DEFAULT_CHANNEL)
    channel_bans = client.get_channel(config.DISCORD_BANS_CHANNEL)

    if config.ENABLE_STARTUP_MSG == True:
        await client.send_message(channel, templates.MSG_ON_CONNECT)

    if config.DISCORD_NOW_PLAYING:
        await client.change_presence(game=discord.Game(name=config.DISCORD_NOW_PLAYING))

    server = client.get_server(config.DISCORD_SERVER)

    # Get the Role object for the given min role name
    for role in server.roles:
        if role.name == config.DISCORD_MIN_ROLE:
            min_role = role
    if min_role == None:
        logger.error('The role DISCORD_MIN_ROLE={} was not found on the server'.format(
            config.DISCORD_MIN_ROLE))

    asyncio.ensure_future(alerter_watcher())
    asyncio.ensure_future(ns2plus_watcher())


@client.event
async def on_message(message):
    """ Wait for !commands """

    global channel
    global min_role

    if client.user == message.author:
        return

    if message.channel.is_private:
        logger.info(f'{message.channel}: {message.content}')

    if message.channel.id in config.DISCORD_LISTEN_CHANNELS or message.channel.is_private:
        if message.content.startswith('!'):
            author_is_admin = False

            for member in client.get_server(config.DISCORD_SERVER).members:
                if member == message.author:
                    if member.top_role >= min_role:
                        author_is_admin = True
                    break

            logger.info(templates.LOG_COMMAND_EXEC.format(message))
            if message.content.startswith('!status'):
                status = game_server.status

                await client.send_message(message.channel, embed=templates.StatusEmbed(status))

            elif message.content.startswith('!comm') and config.ENABLE_STATS:
                params = message.content.split('!comm ')
                try:
                    player = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    await client.send_message(message.channel, embed=templates.CommEmbed(player))

            elif message.content.startswith('!player') and config.ENABLE_STATS:
                params = message.content.split('!player ')
                try:
                    player = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    await client.send_message(message.channel, embed=templates.PlayerEmbed(player))
                    ns2id = templates.NameToNS2ID(player)
                    if ns2id:
                        await client.send_message(message.channel, f'https://ns2sud.com/stats/player/{ns2id}')

            elif message.content.startswith('!top10') and config.ENABLE_STATS:
                params = message.content.split('!top10 ')
                try:
                    type = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    await client.send_message(message.channel, embed=templates.TopEmbed(type))

            elif message.content.startswith('!ns2id') and author_is_admin:
                params = message.content.split('!ns2id ')
                try:
                    input = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    await client.send_message(message.channel, embed=templates.NS2IDEmbed(input))

            elif message.content.startswith('!awards') and config.ENABLE_STATS:
                await client.send_message(message.channel, embed=templates.AwardsEmbed())

            elif message.content.startswith('!say') and author_is_admin:
                params = message.content.split('!say ')
                try:
                    input = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    server_msg_queue.append(
                        templates.POST_RESPONSE_CHAT.format(message.author, input))
                    await client.send_message(message.channel, templates.MSG_ACK)

            elif message.content.startswith('!rcon') and author_is_admin:
                params = message.content.split('!rcon ')
                try:
                    input = params[1]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    server_msg_queue.append(
                        templates.POST_RESPONSE_RCON.format(message.author, input))
                    await client.send_message(message.channel, templates.MSG_ACK)

            elif message.content.startswith('!msg') and author_is_admin:
                params = message.content.split(' ')
                try:
                    channel = params[1]
                    msg = params[2]
                except:
                    await client.send_message(message.channel, templates.MSG_COMMAND_REQUIRES_PARAMS)
                else:
                    await client.send_message(client.get_channel(channel), msg)

            elif message.content.startswith('!help'):
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

    if config.ALERT_EVERYONE_ENABLED:
        while True:
            status = game_server.status
            if config.ALERT_EVERYONE_THRESHOLD_MIN < status.info['player_count'] < config.ALERT_EVERYONE_THRESHOLD_MAX:
                needed_players = config.ALERT_PLAYERCOUNT_START - \
                    status.info['player_count']
                await client.send_message(channel, embed=templates.AlertEveryoneEmbed(needed_players))
                await asyncio.sleep(config.ALERT_EVERYONE_TIME_CAP)
            else:
                await asyncio.sleep(5)


async def ns2plus_watcher():
    """ Periodically check if there is an updated sqlite db available """
    global last_match_id

    if config.DATABASE == 'SQLITE':
        while True:
            try:
                with aiohttp.ClientSession() as session:
                    async with session.get(config.WONITOR_URL + 'query.php?table=RoundInfo&data=count') as r:
                        response = json.loads(await r.read())
                        match_id = int(response[0]['count'])
                        if last_match_id != match_id and last_match_id is not None:
                            logger.info(
                                f'New round with ID {match_id}. Fetching ns2plus DB...')
                            await ns2plus.stats.update()
                        last_match_id = match_id
            except:
                pass
            else:
                await asyncio.sleep(60)


server_msg_queue = []


async def bridge_endpoint(request):
    data = await request.post()

    if 'type' in data:
        if data['type'] == 'chat':
            teams = {'0': 'RR', '1': 'M', '2': 'A', '3': 'S'}
            await client.send_message(channel,
                                      templates.MSG_CHAT.format(teams[data['team']], data['plyr'], data['msg']))
        if data['type'] == 'adminprint' and 'banned' in data['msg']:
            await client.send_message(channel_bans, f'`{data["msg"]}`')

        if data['type'] == 'status':
            if data['sub'] == 'roundstart':
                await client.send_message(channel, templates.MSG_EVENT_ROUNDSTART)
            if data['sub'] == 'marinewin':
                await client.send_message(channel, templates.MSG_EVENT_MARINEWIN)
            if data['sub'] == 'alienwin':
                await client.send_message(channel, templates.MSG_EVENT_ALIENWIN)

    logger.info(f'DiscordBridge POST: {data}')

    if server_msg_queue:
        msg = server_msg_queue[0]
        server_msg_queue.pop(0)
        return web.Response(text=msg)
    else:
        return web.Response()


async def init_webserver(loop):
    app = web.Application(loop=loop)
    app.router.add_route('*', '/', bridge_endpoint)
    return app


async def discord_manager():
    while True:
        try:
            await client.start(config.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Error starting Discord client: {e}")
            pass

        time.sleep(10)


game_server = GameServer(loop, event_handler=on_gameserver_event)

asyncio.ensure_future(discord_manager())

while True:
    try:
        app = loop.run_until_complete(init_webserver(loop))
        web.run_app(app, host='0.0.0.0', port=config.WEBSERVER_PORT)
    except Exception as e:
        logger.error(e)
    time.sleep(5)
