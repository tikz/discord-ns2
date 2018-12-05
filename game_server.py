import asyncio
import logging
import time
from collections import namedtuple

import valve.source.a2s

import config
import utils

logger = logging.getLogger(__name__)
utils.logger_formatter(logger)

ServerStatus = namedtuple('ServerStatus', 'info map players')
Event = namedtuple('Event', 'type value')

game_start_time = 0


class GameServer:
    """ Manages all communication with the game server.

    The only method to access externally is self.status. Sends obj Event to callback event_handler.

    Attributes
    -----------
    status: class ServerStatus
        Attributes: info, map, players
    """

    def __init__(self, loop, event_handler):
        self._server_address = (
            str(config.SERVER_ADDRESS), int(config.SERVER_PORT))

        self._previous_map = None
        self._previous_playerlist = []
        self._map = None
        self._playerlist = None

        self.status = None

        self._event_handler = event_handler

        self.loop = loop
        asyncio.ensure_future(self._refresher())

    async def _refresher(self):
        while True:
            await self._query()
            await asyncio.sleep(config.SERVER_POLL_RATE)

    async def _query(self):
        if self._map:
            self._previous_map = self._map
        if self._playerlist is not None:
            self._previous_playerlist = self._playerlist

        try:
            with valve.source.a2s.ServerQuerier(self._server_address) as server:
                self._info = server.info()
                self._map = self._info.values['map']
                self._players = server.players()['players']
                self._playerlist = [player.values['name']
                                    for player in self._players]
        except Exception as ex:
            logger.debug(ex)
        else:
            self.status = ServerStatus(self._info, self._map, self._players)

        if self._previous_map or self._previous_playerlist:
            await self._event_triggers()

    async def _event_triggers(self):
        global game_start_time
        event_queue = []

        for player in self._previous_playerlist:
            if player not in self._playerlist and player != 'Unknown':
                if 'AFK - ' + player in self._playerlist:
                    event_queue.append(
                        Event('afk', player.replace('AFK - ', '')))
                else:
                    if 'AFK' not in player and player != '':
                        event_queue.append(Event('quit', player))

        for player in self._playerlist:
            if player not in self._previous_playerlist and player != 'Unknown':
                if 'AFK - ' + player in self._previous_playerlist:
                    event_queue.append(Event('nafk', player))
                else:
                    if 'AFK' not in player and player != '':
                        event_queue.append(Event('join', player))

        if self._map != self._previous_map:
            event_queue.append(Event('map_change', self._map))

        if len(self._playerlist) == 0 and game_start_time:
            event_queue.append(Event('rip', time.time() - game_start_time))
            game_start_time = 0

        if len(self._previous_playerlist) == config.ALERT_PLAYERCOUNT_START - 1 \
                and len(self._playerlist) == config.ALERT_PLAYERCOUNT_START:
            event_queue.append(Event('game_start', self._map))
            game_start_time = time.time()

        for event in event_queue:
            logger.info(event)
            await self._event_handler(event)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    game_server = GameServer(loop, event_handler=print)
    loop.run_forever()
